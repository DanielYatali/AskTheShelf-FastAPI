import asyncio
import json
from datetime import datetime

import requests
from fastapi import APIRouter, HTTPException, status, Request, BackgroundTasks

from app.schemas.llm_schema import ActionResponse
from app.utils.utils import make_affiliate_link, make_affiliate_link_from_asin
from app.models.conversation_model import Message
from app.models.product_error_model import ProductError
from app.models.product_model import Product
from app.schemas.job_schema import JobIn, JobOut, JobRequest, JobUpdate
from app.schemas.product_schema import ProductOut, ProductCard, ProductValidateSearch
from app.services.conversation_service import ConversationService
from app.services.job_service import JobService
from app.services.product_service import ProductService, ProductErrorService
from app.services.llm_service import LLMService, GPT3
from app.core.logger import logger

scrapy_router = APIRouter()


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
            case "get_product_details":
                background_tasks.add_task(handle_get_product_details, updated_job)
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


async def handle_compare_products(updated_job):
    try:
        products_data = updated_job.result
        user_conversation = await ConversationService.get_conversation_by_user_id(updated_job.user_id)
        job_id = updated_job.job_id
        products_ids = []
        for product_data in products_data:
            if not product_data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No product data found in job")
            product_id = product_data["product_id"]
            products_ids.append({"product_id": product_id})
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
            embedding_text = await LLMService.generate_embedding_text(product_data)
            embedding = await LLMService.create_embedding(embedding_text)
            new_product.embedding = embedding
            new_product.embedding_text = embedding_text
            new_product.updated_at = datetime.now()
            await ProductService.update_product(product_id, new_product)
        action = ActionResponse(
            action="compare_products",
            user_query=updated_job.user_query,
            products=products_ids
        )
        response = await LLMService.compare_products(action, GPT3, user_conversation.user_id)
        assistant_message = Message(
            role="assistant",
            content=response['message'],
            related_products=response['related_products'],
        )
        user_conversation.messages.append(assistant_message)
        await ConversationService.update_conversation(user_conversation.user_id, user_conversation)
        await JobService.delete_job(job_id)
    except Exception as e:
        logger.error("Error in handle_compare_products: ", e)
        user_conversation = await ConversationService.get_conversation_by_user_id(updated_job.user_id)
        assistant_message = Message(
            role="assistant",
            content="Error comparing products, please try again.",
        )
        user_conversation.messages.append(assistant_message)
        await ConversationService.update_conversation(user_conversation.user_id, user_conversation)


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

        product_ids_json = await LLMService.validate_embedding_search(validate_products, updated_job.user_query)
        validated_products = json.loads(product_ids_json)

        new_product_cards = [card for card in product_cards if card.product_id in validated_products["products"]][:5]
        message_content = validated_products.get("message", "Here are the matching products based on your search.")

        user_conversation = await ConversationService.get_conversation_by_user_id(updated_job.user_id)
        assistant_message = Message(role="assistant", content=message_content, products=new_product_cards)
        user_conversation.messages.append(assistant_message)
        await ConversationService.update_conversation(updated_job.user_id, user_conversation)

        if new_product_cards:
            urls = ["https://www.amazon.com/dp/" + card.product_id for card in new_product_cards]
            action = ActionResponse(action="basic_get_product_details", user_query=updated_job.user_query)
            await JobService.basic_get_products(updated_job.user_id, action, urls)

        await JobService.delete_job(updated_job.job_id)

    except Exception as e:
        logger.error(f"Error in handle_multiple_products: {e}")
        user_conversation = await ConversationService.get_conversation_by_user_id(updated_job.user_id)
        assistant_message = Message(role="assistant", content="Error processing search results, please try again.")
        user_conversation.messages.append(assistant_message)
        await ConversationService.update_conversation(updated_job.user_id, user_conversation)
    # try:
    #     job_id = updated_job.job_id
    #     products = updated_job.result
    #     product_cards = []
    #     validate_products = []
    #
    #     for product in products:
    #         product_data = product
    #         product_id = product_data["product_id"]
    #         if not product_id or product_id == '':
    #             continue
    #         embedding_text = json.dumps(product_data)
    #         affiliate_link = make_affiliate_link_from_asin(product_data["product_id"])
    #         product_data["affiliate_url"] = affiliate_link
    #         product_card = ProductCard(**product_data)
    #         product_validate = ProductValidateSearch(product_id=product_data["product_id"],
    #                                                  embedding_text=embedding_text)
    #         validate_products.append(product_validate)
    #         product_cards.append(product_card)
    #
    #     product_ids = await LLMService.validate_embedding_search(validate_products, updated_job.user_query)
    #     validated_products = json.loads(product_ids)
    #
    #     new_product_cards = []
    #     max_products = 5
    #     for product_card in product_cards:
    #         if len(new_product_cards) >= max_products:
    #             break
    #         if product_card.product_id in validated_products["products"]:
    #             new_product_cards.append(product_card)
    #
    #     user_conversation = await ConversationService.get_conversation_by_user_id(updated_job.user_id)
    #     assistant_message = Message(
    #         role="assistant",
    #         content=validated_products["message"],
    #         products=new_product_cards,
    #     )
    #     user_conversation.messages.append(assistant_message)
    #     await ConversationService.update_conversation(updated_job.user_id, user_conversation)
    #     await JobService.delete_job(updated_job.job_id)
    #     urls = []
    #     product_ids = json.loads(product_ids)
    #     for product in product_ids["products"]:
    #         url = "https://www.amazon.com/dp/" + product
    #         urls.append(url)
    #     action = ActionResponse(
    #         action="basic_get_product_details",
    #         user_query=updated_job.user_query,
    #     )
    #     if len(urls) > 5:
    #         urls = urls[:5]
    #     await JobService.basic_get_products(updated_job.user_id, action, urls)
    #     await JobService.delete_job(job_id)
    #
    # except Exception as e:
    #     logger.error("Error in handle_multiple_products: ", e)
    #     user_conversation = await ConversationService.get_conversation_by_user_id(updated_job.user_id)
    #     assistant_message = Message(
    #         role="assistant",
    #         content="Error processing search results, please try again.",
    #     )
    #     user_conversation.messages.append(assistant_message)


async def handle_get_basic_product_details(updated_job):
    try:
        if not updated_job.result:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No product data found in job")

        product_data_tasks = [process_product_data(product_data, updated_job) for product_data in updated_job.result if
                              product_data]
        await process_in_batches(product_data_tasks, 2)

        await JobService.delete_job(updated_job.job_id)

    except Exception as e:
        logger.error(f"Error in handle_get_basic_product_details: {e}")
        await handle_error_in_conversation(updated_job, message="Error fetching product details, please try again.")


async def process_in_batches(tasks, batch_size):
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i + batch_size]
        await asyncio.gather(*batch)


async def process_product_data(product_data, updated_job):
    product_id = product_data.get("product_id")
    affiliate_url = make_affiliate_link(updated_job.url)
    product_data["affiliate_url"] = affiliate_url

    existing_product = await ProductService.get_product_by_id(product_id)
    if existing_product:
        return

    new_product = Product(**product_data, user_id=updated_job.user_id)
    new_product = await ProductService.create_product(new_product)
    errors = await ProductService.validate_product(new_product)

    if errors:
        await handle_product_errors(product_id, updated_job.job_id, updated_job.user_id, errors)

    embedding_text = await LLMService.generate_embedding_text(product_data)
    embedding = await LLMService.create_embedding(embedding_text)

    new_product.embedding = embedding
    new_product.embedding_text = embedding_text
    new_product.updated_at = datetime.now()

    await ProductService.update_product(product_id, new_product)


async def handle_product_errors(product_id, job_id, user_id, errors):
    new_product_error = ProductError(product_id=product_id, job_id=job_id, user_id=user_id, error=errors)
    await ProductErrorService.create_product_error(new_product_error)


async def handle_error_in_conversation(updated_job, message="Error processing product details, please try again."):
    user_conversation = await ConversationService.get_conversation_by_user_id(updated_job.user_id)
    assistant_message = Message(role="assistant", content=message)
    user_conversation.messages.append(assistant_message)
    await ConversationService.update_conversation(updated_job.user_id, user_conversation)


# async def handle_get_basic_product_details(updated_job):
#     try:
#         products_data = updated_job.result
#         job_id = updated_job.job_id
#         products_ids = []
#         for product_data in products_data:
#             if not product_data:
#                 raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No product data found in job")
#             product_id = product_data["product_id"]
#             products_ids.append({"product_id": product_id})
#             affiliate_url = make_affiliate_link(updated_job.url)
#             product_data["affiliate_url"] = affiliate_url
#             existing_product = await ProductService.get_product_by_id(product_id)
#             if existing_product:
#                 continue
#             new_product = Product(**product_data)
#             new_product.user_id = updated_job.user_id
#             new_product = await ProductService.create_product(new_product)
#             errors = await ProductService.validate_product(new_product)
#             if len(errors) > 0:
#                 new_product_error = ProductError(
#                     product_id=product_id,
#                     job_id=job_id,
#                     user_id=updated_job.user_id,
#                     error=errors,
#                 )
#                 await ProductErrorService.create_product_error(new_product_error)
#             embedding_text = await LLMService.generate_embedding_text(product_data)
#             embedding = await LLMService.create_embedding(embedding_text)
#             new_product.embedding = embedding
#             new_product.embedding_text = embedding_text
#             new_product.updated_at = datetime.now()
#             await ProductService.update_product(product_id, new_product)
#         await JobService.delete_job(job_id)
#     except Exception as e:
#         logger.error("Error in handle_get_basic_product_details: ", e)
#         user_conversation = await ConversationService.get_conversation_by_user_id(updated_job.user_id)
#         assistant_message = Message(
#             role="assistant",
#             content="Error fetching product details, please try again.",
#         )
#         user_conversation.messages.append(assistant_message)
#         await ConversationService.update_conversation(user_conversation.user_id, user_conversation)


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
    embedding_text = await LLMService.generate_embedding_text(product_data)
    embedding = await LLMService.create_embedding(embedding_text)
    # new_product.generated_review = generated_review
    new_product.embedding = embedding
    new_product.embedding_text = embedding_text
    new_product.updated_at = datetime.now()
    await ProductService.update_product(product_id, new_product)
    await JobService.delete_job(job_id)


@scrapy_router.get("/update")
async def run_spider():
    scrapyd_url = "http://localhost:6800/schedule.json"  # Adjust if Scrapyd is not running on localhost
    data = {
        'project': 'default',
        'spider': 'amazon',
        'url': 'https://www.amazon.com/dp/B07VGRJDFY',
        'job_id': '12345'
    }
    response = requests.post(scrapyd_url, data=data)
    if response.status_code == 200:
        # Scrapyd successfully accepted the request
        return response.json()
    else:
        # Something went wrong
        raise HTTPException(status_code=response.status_code, detail="Scrapyd failed to schedule the spider")
