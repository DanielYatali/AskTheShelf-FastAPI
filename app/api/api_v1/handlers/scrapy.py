import asyncio
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Request, BackgroundTasks
from app.core.config import manager
from app.schemas.llm_schema import ActionResponse
from app.utils.utils import make_affiliate_link, make_affiliate_link_from_asin, parse_json
from app.models.conversation_model import Message
from app.models.product_error_model import ProductError
from app.models.product_model import Product
from app.schemas.job_schema import JobIn, JobOut, JobRequest, JobUpdate
from app.schemas.product_schema import ProductOut, ProductCard, ProductValidateSearch
from app.services.conversation_service import ConversationService
from app.services.job_service import JobService
from app.services.product_service import ProductService, ProductErrorService
from app.services.llm_service import LLMService, GPT3, GEMINI_EMBEDDING, OPEN_AI_EMBEDDING, GEMINI, RequestContext
from app.core.logger import logger

scrapy_router = APIRouter()


# the webscraper will send a POST request to this endpoint once it has finished its job
@scrapy_router.post("/update", summary="Update job")
async def update_job(request: Request, job: dict, background_tasks: BackgroundTasks):
    try:
        job_data = job
        job_id = job["job_id"]
        old_job = await JobService.get_job_by_id(job_id)
        if not old_job:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job not found")
        job["user_id"] = old_job.user_id
        job = JobUpdate(**job)
        job.status = "completed"
        result = job.result
        if not result:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No result found")
        update_job.result = ["completed"]
        updated_job = await JobService.update_job(job_id, job)
        if not updated_job:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job not found")
        # Adding the long-running tasks to the background
        updated_job.result = result
        match updated_job.action:
            case "link":
                background_tasks.add_task(handle_links, updated_job)
            case "search":
                background_tasks.add_task(handle_search_products, updated_job)
            case "basic_get_product_details":
                background_tasks.add_task(handle_get_basic_product_details, updated_job)
        # Immediately return a response to the client
        return {"status": "success", "message": "Product creation process started"}

    except Exception as e:
        logger.error("Error in update_job: ", e)
        job_id = job_data["job_id"]
        old_job = await JobService.get_job_by_id(job_id)
        await handle_error_in_conversation(old_job, message="Error processing results, please try again.")
        return {"status": "failed", "message": "Error processing results, please try again"}


async def handle_search_products(updated_job):
    try:
        product_cards = []
        validate_products = []
        for product in updated_job.result:
            product_id = product.get("product_id", "")
            if product_id:
                product["affiliate_url"] = make_affiliate_link_from_asin(product_id)
                product_cards.append(ProductCard(**product))
                embedding_text = json.dumps(product)
                validate_products.append(ProductValidateSearch(product_id=product_id, embedding_text=embedding_text))

        user_conversation = await ConversationService.get_conversation_by_user_id(updated_job.user_id)
        product_ids_json = await LLMService.validate_embedding_search(validate_products, user_conversation,
                                                                      updated_job.user_query)
        validated_products = parse_json(product_ids_json)
        if not validated_products and validate_products != []:
            product_ids_json = await LLMService.validate_embedding_search(validate_products, user_conversation,
                                                                          updated_job.user_query)
            validated_products = parse_json(product_ids_json)
            if not validated_products and validate_products != []:
                logger.error("Bad response from LLM")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad response from LLM")

        new_product_cards = [card for card in product_cards if card.product_id in validated_products["products"]][:5]
        message_content = validated_products.get("message", "Here are the matching products based on your search.")

        assistant_message = Message(role="assistant", content=message_content, products=new_product_cards)
        user_conversation.messages.append(assistant_message)
        await ConversationService.update_conversation(updated_job.user_id, user_conversation)
        await manager.send_personal_json(assistant_message.json(), user_conversation.user_id)

        if new_product_cards:
            urls = ["https://www.amazon.com/dp/" + card.product_id for card in new_product_cards]
            action = ActionResponse(action="basic_get_product_details", user_query=updated_job.user_query)
            await JobService.basic_get_products(updated_job.user_id, action, urls)
            assistant_message = Message(role="assistant",
                                        content="We will fetch products details in the background for you. This may take a few seconds.")
        await manager.send_personal_json(assistant_message.json(), user_conversation.user_id)
        await JobService.delete_job(updated_job.job_id)

    except Exception as e:
        logger.error(f"Error in handle_multiple_products: {e}")
        user_conversation = await ConversationService.get_conversation_by_user_id(updated_job.user_id)
        assistant_message = Message(role="assistant", content="Error processing search results, please try again.")
        user_conversation.messages.append(assistant_message)
        await ConversationService.update_conversation(updated_job.user_id, user_conversation)
        await manager.send_personal_json(assistant_message.json(), user_conversation.user_id)


async def handle_get_basic_product_details(updated_job):
    try:
        if not updated_job.result:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No product data found in job")

        product_data_tasks = []
        use_gemini = True

        for product_data in updated_job.result:
            if product_data:
                # Split up the tasks between the two models
                # OpenAI seems to timeout on multiple requests
                embedding_model = GEMINI_EMBEDDING if use_gemini else OPEN_AI_EMBEDDING
                model = GEMINI if use_gemini else GPT3
                task = process_product_data(product_data, updated_job, embedding_model=embedding_model, llm_model=model)
                product_data_tasks.append(task)
                use_gemini = not use_gemini
        # Process the tasks in batches of 2
        # This is to prevent timeouts
        # TODO right now is this is the longest operation in the codebase
        # Look into ways to speed this up
        await process_in_batches(product_data_tasks, 2)

        await JobService.delete_job(updated_job.job_id)

    except Exception as e:
        logger.error(f"Error in handle_get_basic_product_details: {e}")
        await handle_error_in_conversation(updated_job, message="Error fetching product details, please try again.")


async def process_in_batches(tasks, batch_size):
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i + batch_size]
        await asyncio.gather(*batch)


async def process_product_data(product_data, updated_job, embedding_model=OPEN_AI_EMBEDDING, llm_model=GPT3):
    try:
        product_id = product_data.get("product_id")
        affiliate_url = make_affiliate_link_from_asin(product_id)
        product_data["affiliate_url"] = affiliate_url

        existing_product = await ProductService.get_product_by_id(product_id)
        if existing_product:
            return

        new_product = Product(**product_data, user_id=updated_job.user_id)
        new_product = await ProductService.create_product(new_product)
        errors = await ProductService.validate_product(new_product)

        if errors:
            await handle_product_errors(product_id, updated_job.job_id, updated_job.user_id, errors)

        embedding_text = await LLMService.generate_embedding_text(product_data, llm_model)
        # Needs to be OpenAI for now because the dimensions are already indexed with 1536 dimensions
        embedding = await LLMService.create_embedding(embedding_text, OPEN_AI_EMBEDDING)

        new_product.embedding = embedding
        new_product.embedding_text = embedding_text
        new_product.updated_at = datetime.now()

        await ProductService.update_product(product_id, new_product)
    except Exception as e:
        title = product_data.get("title")
        logger.error(f"Error in process_product_data: {e}")
        await handle_error_in_conversation(updated_job,
                                           message=f"Error processing product details for {title}, please try again.")


async def handle_product_errors(product_id, job_id, user_id, errors):
    new_product_error = ProductError(product_id=product_id, job_id=job_id, user_id=user_id, error=errors)
    await ProductErrorService.create_product_error(new_product_error)


async def handle_error_in_conversation(updated_job, message="Error processing product details, please try again."):
    user_conversation = await ConversationService.get_conversation_by_user_id(updated_job.user_id)
    assistant_message = Message(role="assistant", content=message)
    user_conversation.messages.append(assistant_message)
    await ConversationService.update_conversation(updated_job.user_id, user_conversation)
    await manager.send_personal_json(assistant_message.json(), user_conversation.user_id)


async def handle_get_product_details(updated_job):
    try:
        product_data = updated_job.result[0]
        user_conversation = await ConversationService.get_conversation_by_user_id(updated_job.user_id)
        job_id = updated_job.job_id
        if not product_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No product data found in job")
        product_id = product_data["product_id"]
        affiliate_url = make_affiliate_link(updated_job.url)
        product_data["affiliate_url"] = affiliate_url
        existing_product = await ProductService.get_product_by_id(product_id)
        if existing_product:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product already exists")
        new_product = Product(**product_data)
        new_product.user_id = updated_job.user_id
        new_product = await ProductService.create_product(new_product)
        errors = await ProductService.validate_product(new_product)
        if len(errors) > 0:
            new_product_error = ProductError(
                product_id=product_id,
                job_id=job_id,
                user_id=updated_job.user_id,
                error=errors,
            )
            await ProductErrorService.create_product_error(new_product_error)
        action = ActionResponse(
            action="get_product_details",
            user_query=updated_job.user_query,
            product_id=new_product.product_id
        )
        response = await LLMService.get_product_details(action, GPT3, user_conversation.user_id)
        assistant_message = Message(
            role="assistant",
            content=response['message'],
            related_products=response['related_products'],
        )
        user_conversation.messages.append(assistant_message)
        await ConversationService.update_conversation(user_conversation.user_id, user_conversation)
        embedding_text = await LLMService.generate_embedding_text(product_data)
        embedding = await LLMService.create_embedding(embedding_text)
        new_product.embedding = embedding
        new_product.embedding_text = embedding_text
        new_product.updated_at = datetime.now()
        await ProductService.update_product(product_id, new_product)
        await JobService.delete_job(job_id)
    except Exception as e:
        logger.error("Error in handle_get_product_details: ", e)
        user_conversation = await ConversationService.get_conversation_by_user_id(updated_job.user_id)
        assistant_message = Message(
            role="assistant",
            content="Error processing product details, please try again.",
        )
        user_conversation.messages.append(assistant_message)
        await ConversationService.update_conversation(user_conversation.user_id, user_conversation)


async def handle_links(updated_job):
    try:
        product_data = updated_job.result[0]
        job_id = updated_job.job_id
        if not product_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No product data found in job")
        product_id = product_data["product_id"]
        affiliate_url = make_affiliate_link(updated_job.url)
        product_data["affiliate_url"] = affiliate_url
        existing_product = await ProductService.get_product_by_id(product_id)
        if existing_product:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product already exists")
        new_product = Product(**product_data)
        new_product.user_id = updated_job.user_id
        user_conversation = await ConversationService.get_conversation_by_user_id(new_product.user_id)
        productOut = ProductCard(**new_product.dict())
        assistant_message = Message(
            role="assistant",
            content="Here is the product you requested",
            products=[productOut],
        )
        user_conversation.messages.append(assistant_message)
        await ConversationService.update_conversation(new_product.user_id, user_conversation)
        await manager.send_personal_json(assistant_message.json(), user_conversation.user_id)
        new_product = await ProductService.create_product(new_product)
        errors = await ProductService.validate_product(new_product)
        if len(errors) > 0:
            new_product_error = ProductError(
                product_id=product_id,
                job_id=job_id,
                user_id=updated_job.user_id,
                error=errors,
            )
            await ProductErrorService.create_product_error(new_product_error)

        # generated_review, embedding_text = await asyncio.gather(
        #     LLMService.generate_product_review(product_data),
        #     LLMService.generate_embedding_text(product_data)
        # )
        embedding_text = await LLMService.generate_embedding_text(product_data, GEMINI)
        embedding = await LLMService.create_embedding(embedding_text, GEMINI_EMBEDDING)
        # new_product.generated_review = generated_review
        new_product.embedding = embedding
        new_product.embedding_text = embedding_text
        new_product.updated_at = datetime.now()
        await ProductService.update_product(product_id, new_product)
        await JobService.delete_job(job_id)
    except Exception as e:
        logger.error("Error in handle_links: ", e)
        user_conversation = await ConversationService.get_conversation_by_user_id(updated_job.user_id)
        assistant_message = Message(
            role="assistant",
            content="Error processing product details, please try again.",
        )
        user_conversation.messages.append(assistant_message)
        await ConversationService.update_conversation(updated_job.user_id, user_conversation)
        await manager.send_personal_json(assistant_message.json(), user_conversation.user_id)
