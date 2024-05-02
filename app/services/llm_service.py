import json
from typing import List, Optional

import aiofiles
import httpx
from fastapi import HTTPException
from groq import Groq
from openai import OpenAI

from app.core.config import manager
from app.core.config import settings
from app.core.logger import logger
from app.models.conversation_model import Conversation, Message
from app.models.product_model import Product
from app.schemas.llm_schema import ActionResponse
from app.schemas.product_schema import ProductValidateSearch, ProductCard, product_identifier_serializer
from app.services.conversation_service import ConversationService
from app.services.job_service import JobService
from app.services.product_service import ProductService
import google.generativeai as genai

GPT3 = "gpt-3.5-turbo"
OPEN_AI_EMBEDDING = "text-embedding-ada-002"
GEMINI = "gemini-pro"
# Tried llama it did a terrible job with json
Llama = "Llama3-8b-8192"
GEMINI_EMBEDDING = "text-embedding-004"


class LLMService:
    @staticmethod
    async def find_similar_embeddings(collection, embedding: List[float], excludes: List[str], query: str,
                                      limit: int = 1, model: Optional[str] = None
                                      ):
        try:
            # Build the pipeline for vector search
            pipeline = [
                {
                    "$vectorSearch": {
                        "queryVector": embedding,
                        "path": "embedding",
                        "numCandidates": 100,
                        "limit": limit,
                        "index": "vector_index",
                    }
                },
                {
                    "$project": {
                        "score": {"$meta": "vectorSearchScore"},
                        **{field: 0 for field in excludes}
                    }
                }
            ]

            # Run the aggregation
            documents_cursor = collection.aggregate(pipeline)
            products = []
            old_documents = []

            async for doc in documents_cursor:
                product = ProductValidateSearch(**doc)
                products.append(product)
                old_documents.append(doc)

            # If products were found, validate them using LLM
            if products:
                try:
                    response = await LLMService.validate_embedding_search(products, query, model)
                    response_data = json.loads(response)
                    validated_products_ids = response_data.get("products", [])
                    message = response_data.get("message", "")
                except Exception as e:
                    logger.error("Error validating embeddings with LLM " + str(e))
                    raise HTTPException(status_code=500, detail="Error validating embeddings with LLM")

                # Filter the products based on the validated IDs
                filtered_products = [
                    doc for doc in old_documents
                    if doc['product_id'] in validated_products_ids
                ]
                return filtered_products, message

            return [], ""

        except Exception as e:
            logger.error("Error in find_similar_embeddings " + str(e), exc_info=True)
            raise HTTPException(status_code=500, detail="Error in find_similar_embeddings")

    @staticmethod
    async def validate_embedding_search(products: list[ProductValidateSearch], query, model=None):
        try:
            async with aiofiles.open('prompts/validate_embedding_search_prompt.txt', mode='r') as file:
                prompt = await file.read()
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user",
                 "content": f"{products}"},
                {"role": "user", "content": query}
            ]
            return await LLMService.llm_request(messages, model)
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=500, detail="Error in validate_embedding_search")

    @staticmethod
    async def create_open_ai_embedding(query, model=None):
        try:
            url = 'https://api.openai.com/v1/embeddings'
            openai_key = settings.OPENAI_API_KEY
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers={
                    'Authorization': f'Bearer {openai_key}',
                    'Content-Type': 'application/json'
                }, json={
                    'input': query,
                    'model': 'text-embedding-ada-002'
                })

                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail="Error from OpenAI API")

                response_data = response.json()
                embedding = response_data['data'][0]['embedding']
                return embedding
        except Exception as e:
            logger.error("Error in create_embedding", e)
            raise HTTPException(status_code=500, detail="Error in create_embedding")

    @staticmethod
    async def create_embedding(query, model=None):
        try:
            # if model is None:
            #     model = OPEN_AI_EMBEDDING
            # if model == OPEN_AI_EMBEDDING:
            return await LLMService.create_open_ai_embedding(query, model)
            # elif model == GEMINI_EMBEDDING:
            #     return await LLMService.create_gemini_embedding(query, model)

        except Exception as e:
            logger.error("Error in create_embedding", e)
            raise HTTPException(status_code=500, detail="Error in create_embedding")

    @staticmethod
    async def generate_product_review(product):
        try:
            # Read the prompt asynchronously
            # check the length of the product review array
            promptFile = "prompts/reviews_prompt.txt"
            if len(product["reviews"]) == 0:
                promptFile = "prompts/no_reviews_prompt.txt"
            async with aiofiles.open(promptFile, mode='r') as file:
                prompt = await file.read()

            product.pop("embedding", None)
            product.pop("similar_products", None)
            product.pop("qa", None)
            product.pop("embedding_text", None)
            product.pop("user_id", None)
            product.pop("updated_at", None)
            product.pop("created_at", None)
            # Configure your OpenAI client properly here
            client = OpenAI()

            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user",
                     "content": f"{product}"}
                ]
            )
            message = completion.choices[0].message.model_dump()
            return message["content"]

        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=500, detail="Error in generate_product_review")

    @staticmethod
    async def generate_embedding_text(product, model):
        try:
            # Read the prompt asynchronously
            async with aiofiles.open('prompts/embedding_text_prompt.txt', mode='r') as file:
                prompt = await file.read()

            # Configure your OpenAI client properly here
            product.pop("embedding", None)
            product.pop("reviews", None)
            product.pop("similar_products", None)
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user",
                 "content": f"{product}"}
            ]
            return await LLMService.llm_request(messages, model)
        except Exception as e:
            logger.error("Error in generate_embedding_text", e)
            raise HTTPException(status_code=500, detail="Error in generate_embedding_text")

    @staticmethod
    async def product_chat(product, query, model):
        try:
            async with aiofiles.open('prompts/product_chat_prompt.txt', mode='r') as file:
                prompt = await file.read()
            product.pop("embedding", None)

            messages = [
                {"role": "system", "content": prompt},
                {"role": "user",
                 "content": f"{product}"},
                {"role": "user", "content": query}
            ]
            response = await LLMService.llm_request(messages, model)
            return response
        except Exception as e:
            logger.error("Error in product_chat", e)
            raise HTTPException(status_code=500, detail="Error in product_chat")

    @staticmethod
    async def make_llm_request(conversation):
        try:
            client = OpenAI()
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=conversation
            )
            message = completion.choices[0].message.model_dump()
            return message["content"]
        except Exception as e:
            logger.error("Error in make_llm_request", e)
            raise HTTPException(status_code=500, detail="Error in make_llm_request")

    @staticmethod
    async def make_openai_request(conversation, model=GPT3):
        try:
            client = OpenAI()
            completion = client.chat.completions.create(
                model=model,
                messages=conversation
            )
            message = completion.choices[0].message.model_dump()
            return message["content"]
        except Exception as e:
            logger.error("Error in make_openai_request", e)
            raise HTTPException(status_code=500, detail="Error in make_openai_request")

    @staticmethod
    async def make_gemini_request(conversation, model=GEMINI):
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(model)
            response = await model.generate_content_async(json.dumps(conversation))
            return response.text
        except Exception as e:
            logger.error("Error in make_gemini_request", e)
            raise HTTPException(status_code=500, detail="Error in make_gemini_request")

    @staticmethod
    async def make_groq_request(conversation, model=Llama):
        try:
            client = Groq(
                api_key=settings.GROQ_API_KEY,
            )
            chat_completion = client.chat.completions.create(
                messages=conversation,
                model=model
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error("Error in make_groq_request", e)
            raise HTTPException(status_code=500, detail="Error in make_groq_request")

    @staticmethod
    async def create_gemini_embedding(query, model=GEMINI_EMBEDDING):
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            result = genai.embed_content(
                model="models/" + model,
                content=query,
                task_type="retrieval_document",
                title="Embedding of list of strings")
            return result.get("embedding", [])
        except Exception as e:
            logger.error("Error in create_gemini_embedding", e)
            raise HTTPException(status_code=500, detail="Error in create_gemini_embedding")

    @staticmethod
    async def llm_request(conversation, model=GPT3):
        try:
            if model == GPT3:
                return await LLMService.make_openai_request(conversation, GPT3)
            elif model == GEMINI:
                return await LLMService.make_gemini_request(conversation, GEMINI)
            elif model == Llama:
                return await LLMService.make_groq_request(conversation, Llama)
            return await LLMService.make_openai_request(conversation, GPT3)
        except Exception as e:
            logger.error("Error in llm_request", e)
            raise HTTPException(status_code=500, detail="Error in llm_request")

    @staticmethod
    async def compare(product1, product2, user_query, model):
        try:
            async with aiofiles.open('prompts/compare_products_prompt.txt', mode='r') as file:
                prompt = await file.read()
            product1.pop("embedding", None)
            product2.pop("embedding", None)
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user",
                 "content": f"{product1}"},
                {"role": "user",
                 "content": f"{product2}"},
                {"role": "user", "content": user_query}
            ]
            return await LLMService.llm_request(messages, model)
        except Exception as e:
            logger.error("Error in compare", e)
            raise HTTPException(status_code=500, detail="Error in compare")

    @staticmethod
    async def manager(query, conversation: Conversation, model):
        try:
            async with aiofiles.open('prompts/manager.txt', mode='r') as file:
                prompt = await file.read()
            context = []
            for message in conversation.messages[-6:]:
                if message.products:
                    context.append({"role": message.role, "content": f'{message.products}'})
                else:
                    context.append({"role": message.role, "content": message.content})
            messages = [
                {"role": "system", "content": prompt},
                *context,
                {"role": "user", "content": query}
            ]
            response = await LLMService.llm_request(messages, model)
            logger.info("Response from LLM:" + response)
            if "action" not in response:
                logger.info("LLM did not return an action, trying again")
                messages.append({"role": "system", "content": response})
                messages.append({"role": "user", "content": "You did not return an action, please try again"})
                response = await LLMService.llm_request(messages, model)
                logger.info("Corrected response from LLM:" + response)
            if "action" in response:
                try:
                    response = json.loads(response)
                    return response
                except json.JSONDecodeError as e:
                    logger.info("Invalid JSON response from LLM", e)
                    messages.append({"role": "system", "content": response})
                    messages.append({"role": "user", "content": "Invalid JSON response please try again"})
                    response = await LLMService.llm_request(messages, model)
                    logger.info("Corrected response from LLM:" + response)
            response = json.loads(response)
            return response
        except Exception as e:
            logger.error("Error in manager", e)
            raise HTTPException(status_code=500, detail="Error in manager")

    @staticmethod
    async def find_similar(action_response: ActionResponse, model: str):
        try:
            if action_response.product_id and action_response.product_id != "":
                product = await ProductService.get_product_by_id(action_response.product_id)
                embedding = product.embedding
                excludes = [
                    "_id",
                    "reviews",
                    "embedding",
                    "qa"
                ]
                documents, message = await LLMService.find_similar_embeddings(Product.get_motor_collection(), embedding,
                                                                              excludes,
                                                                              action_response.embedding_query, 5, model)
                # documents, message = await LLMService.find_similar_embeddings(Product.get_motor_collection(),
                #                                                               embedding,
                #                                                               excludes,
                #                                                               actionResponse.embedding_query, 5,
                #                                                               model)
                if len(documents) == 0:
                    return ("No similar products found, we may not have that product in our database yet, "
                            "try using the link feature to add it")
                productCards = []
                for product in documents:
                    productCards.append(ProductCard(**product.dict()))
                return productCards
            elif action_response.embedding_query and action_response.embedding_query != "":
                embedding = await LLMService.create_embedding(action_response.embedding_query, model)
                excludes = [
                    "_id",
                    "reviews",
                    "embedding",
                    "qa"
                ]
                documents, message = await LLMService.find_similar_embeddings(Product.get_motor_collection(), embedding,
                                                                              excludes,
                                                                              action_response.embedding_query, 5, model)
                if len(documents) == 0:
                    return ("No similar products found, we may not have that product in our database yet, "
                            "try using the link feature to add it")

                productCards = []
                for product in documents:
                    productCards.append(ProductCard(**product))
                return {"products": productCards, "message": message}
        except Exception as e:
            logger.error("Error in find_similar", e)
            raise HTTPException(status_code=500, detail="Error in find_similar")

    @staticmethod
    async def get_product_details(action_response: ActionResponse, model: str, user_id: str):
        try:
            if action_response.product_id and action_response.product_id != "":
                product = await ProductService.get_product_by_id(action_response.product_id)
                if product is None:
                    return ("Product details not found, if a search on amazon was previously initiated, we may still "
                            "be gathering the details, please wait..., if issue persists, please try again later.")
                # A bit too complicated for now can be added in future features
                # if not product:
                #     url = f"https://www.amazon.com/dp/{action_response.product_id}"
                #     await JobService.get_product_details(user_id=user_id, action=action_response, urls=[url])
                #     return "Gathering product details, please wait..."
                response = await LLMService.product_chat(product.dict(), action_response.user_query, model)
                product_identifier = product_identifier_serializer(product.dict())
                return {"related_products": [product_identifier], "message": response}
            elif action_response.embedding_query and action_response.embedding_query != "":
                embedding = await LLMService.create_embedding(action_response.embedding_query)
                excludes = [
                    "_id",
                    "reviews",
                    "embedding",
                    "qa"
                ]
                documents, message = await LLMService.find_similar_embeddings(Product.get_motor_collection(), embedding,
                                                                              excludes,
                                                                              action_response.embedding_query, 1)
                if len(documents) == 0:
                    return ("No similar product found, we may not have that product in our database yet, "
                            "try using the link feature to add it")
                product = documents[0]
                productCard = ProductCard(**product)
                response = await LLMService.product_chat(product, action_response.user_query, model)
                return {"products": [productCard], "message": response}
        except Exception as e:
            logger.error("Error in get_product_details", e)
            raise HTTPException(status_code=500, detail="Error in get_product_details")

    @staticmethod
    async def compare_products(action_response: ActionResponse, model: str, user_id: str):
        try:
            if action_response.products and len(action_response.products) > 0:
                if len(action_response.products) > 2:
                    return "You cannot compare more than 2 products at a time"
                product1Id = action_response.products[0]["product_id"]
                product2Id = action_response.products[1]["product_id"]
                excludes = [
                    "_id",
                    "embedding",
                    "qa"
                ]
                product1 = None
                product2 = None
                if product1Id != "":
                    product1 = await ProductService.get_product_by_id(product1Id)
                    # A bit too complicated for now can be added in future features
                    # if not product1:
                    #     url1 = f"https://www.amazon.com/dp/{product1Id}"
                    #     url2 = f"https://www.amazon.com/dp/{product2Id}"
                    #     await JobService.get_product_details(user_id=user_id, action=action_response, urls=[url1, url2])
                    #     return "Gathering product details, please wait..."
                    product1 = product1.dict()
                else:
                    product1Name = action_response.products[0]["product_name"]
                    if product1Name != "":
                        product1_embedding = await LLMService.create_embedding(product1Name)
                        product1_documents, message = await LLMService.find_similar_embeddings(
                            Product.get_motor_collection(),
                            product1_embedding,
                            excludes, action_response.embedding_query, 1, model)
                        if len(product1_documents) == 0:
                            return (
                                "No similar product found, we may not have that product in our database yet, "
                                "try using the link feature to add it")
                        product1 = product1_documents[0]

                if product2Id != "":
                    product2 = await ProductService.get_product_by_id(product2Id)
                    # A bit too complicated for now can be added in future features
                    # if not product2:
                    #     url1 = f"https://www.amazon.com/dp/{product1Id}"
                    #     url2 = f"https://www.amazon.com/dp/{product2Id}"
                    #     await JobService.get_product_details(user_id=user_id, action=action_response, urls=[url1, url2])
                    #     return "Gathering product details, please wait..."
                    product2 = product2.dict()
                else:
                    product2Name = action_response.products[1]["product_name"]
                    product2_embedding = await LLMService.create_embedding(product2Name)

                    product2_documents, message = await LLMService.find_similar_embeddings(
                        Product.get_motor_collection(),
                        product2_embedding,
                        excludes,
                        action_response.embedding_query,
                        1, model)
                    if len(product2_documents) == 0:
                        return ("No similar product found, we may not have that product in our database yet, "
                                "try using the link feature to add it")
                    product2 = product2_documents[0]
                response = await LLMService.compare(product1, product2, action_response.user_query, model)
                product1Identifier = product_identifier_serializer(product1)
                product2Identifier = product_identifier_serializer(product2)
                return {"related_products": [product1Identifier, product2Identifier], "message": response}
        except Exception as e:
            logger.error("Error in compare_products", e)
            raise HTTPException(status_code=500, detail="Error in compare_products")

    # TODO: Refactor this to return a Message object
    @staticmethod
    async def get_action_from_llm(query, conversation: Conversation, model):
        try:
            response = await LLMService.manager(query, conversation, model)
            if "action" not in response:
                return response
            actionResponse = ActionResponse(**response)
            match actionResponse.action:
                case "none":
                    logger.info("In none case")
                    if actionResponse.response:
                        return actionResponse.response
                case "more_info":
                    logger.info("In more_info case")
                    if actionResponse.response:
                        return actionResponse.response
                case "get_product_details":
                    logger.info("In get_product_details case")
                    return await LLMService.get_product_details(actionResponse, model, conversation.user_id)
                case "find_similar":
                    logger.info("In find_similar case")
                    return await LLMService.find_similar(actionResponse, model)
                case "compare_products":
                    logger.info("In compare_products case")
                    return await LLMService.compare_products(actionResponse, model, conversation.user_id)
                case "search":
                    logger.info("In search case")

                    if actionResponse.embedding_query and actionResponse.embedding_query != "":
                        embedding = await LLMService.create_embedding(actionResponse.embedding_query)
                        excludes = [
                            "_id",
                            "reviews",
                            "embedding",
                            "qa"
                        ]
                        documents, message = await LLMService.find_similar_embeddings(Product.get_motor_collection(),
                                                                                      embedding,
                                                                                      excludes,
                                                                                      actionResponse.embedding_query, 5,
                                                                                      model)
                        if len(documents) == 0:
                            job = await JobService.search_amazon_products(actionResponse.embedding_query,
                                                                          conversation.user_id,
                                                                          query)
                            if job:
                                return ("No similar products found in our database, we are searching Amazon for you, "
                                        "please wait...")
                            return "No similar products found, we may not have that product in our database yet"
                        productCards = []
                        for product in documents:
                            productCards.append(ProductCard(**product))
                        return {"products": productCards, "message": message}
            return "I'm sorry, I don't understand that request"
        except Exception as e:
            logger.error("Error in get_action_from_llm", e)
            assistant_message = Message(
                role="assistant",
                content="I'm sorry, I encountered an error while processing your request"
            )
            conversation.messages.append(assistant_message)
            await ConversationService.update_conversation(conversation.user_id, conversation)
            await manager.send_personal_json(assistant_message.json(), conversation.user_id)
            raise HTTPException(status_code=500, detail="Error in get_action_from_llm")
