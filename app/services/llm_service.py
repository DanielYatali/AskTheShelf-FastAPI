import json

import aiofiles
import httpx
from fastapi import HTTPException
from openai import OpenAI

from app.config.database import product_collection
from app.core.config import settings
from app.core.logger import logger
from app.models.conversation_model import Conversation
from app.schemas.llm_schema import ActionResponse
from app.schemas.product_schema import ProductValidateSearch, ProductCard,product_identifier_serializer
from app.services.product_service import ProductService


class LLMService:
    @staticmethod
    async def find_similar_embeddings(collection, embedding, excludes, query, limit=1):
        try:
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
                {"$project": {"score": {"$meta": "vectorSearchScore"},
                              **{field: 0 for field in excludes}}},
            ]

            documents = collection.aggregate(pipeline)
            # if documents is not none we will make a call the llm to validate the product to see if it matches the query
            if documents is not None:
                products = []
                oldDocuments = []
                for doc in documents:
                    products.append(ProductValidateSearch(**doc))
                    oldDocuments.append(doc)
                if len(products) > 0:
                    response = await LLMService.validate_embedding_search(products, query)
                    response = json.loads(response)
                    products = response["products"]
                    filteredProducts = []
                    for product_id in products:
                        for product in oldDocuments:
                            if product['product_id'] == product_id:
                                filteredProducts.append(product)
                    message = ""
                    if response["message"]:
                        message = response["message"]
                    return filteredProducts, message
            return []
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=500, detail="Error in find_similar_embeddings")

    @staticmethod
    async def validate_embedding_search(products: list[ProductValidateSearch], query):
        try:

            async with aiofiles.open('prompts/validate_embedding_search_prompt.txt', mode='r') as file:
                prompt = await file.read()

            client = OpenAI()
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user",
                     "content": f"{products}"},
                    {"role": "user", "content": query}
                ]
            )
            message = completion.choices[0].message.model_dump()
            return message["content"]
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=500, detail="Error in validate_embedding_search")

    @staticmethod
    async def create_embedding(query):
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
    async def generate_embedding_text(product):
        try:
            # Read the prompt asynchronously
            async with aiofiles.open('prompts/embedding_text_prompt.txt', mode='r') as file:
                prompt = await file.read()

            # Configure your OpenAI client properly here
            client = OpenAI()
            product.pop("embedding", None)
            product.pop("reviews", None)

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
            raise HTTPException(status_code=500, detail="Error in generate_embedding_text")

    @staticmethod
    async def product_chat(product, query):
        async with aiofiles.open('prompts/product_chat_prompt.txt', mode='r') as file:
            prompt = await file.read()
        client = OpenAI()
        product.pop("embedding", None)

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user",
                 "content": f"{product}"},
                {"role": "user", "content": query}
            ]
        )
        message = completion.choices[0].message.model_dump()
        return message["content"]

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
            logger.error(e)
            raise HTTPException(status_code=500, detail="Error in make_llm_request")

    @staticmethod
    async def compare_products(product1, product2, user_query):
        async with aiofiles.open('prompts/compare_products_prompt.txt', mode='r') as file:
            prompt = await file.read()
        client = OpenAI()
        product1.pop("embedding", None)
        product2.pop("embedding", None)

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user",
                 "content": f"{product1}"},
                {"role": "user",
                 "content": f"{product2}"},
                {"role": "user", "content": user_query}
            ]
        )
        message = completion.choices[0].message.model_dump()
        return message["content"]

    @staticmethod
    async def manager(query, conversation: Conversation):
        async with aiofiles.open('prompts/manager.txt', mode='r') as file:
            prompt = await file.read()
        client = OpenAI()
        context = []
        for message in conversation.messages[-6:]:
            if message.products:
                context.append({"role": message.role, "content": f'{message.products}'})
            else:
                context.append({"role": message.role, "content": message.content})

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                *context,
                {"role": "user", "content": query}
            ]
        )
        message = completion.choices[0].message.model_dump()
        return message["content"]

    @staticmethod
    async def get_action_from_llm(query, conversation: Conversation):
        try:
            response = await LLMService.manager(query, conversation)
            logger.info("Response from manager:" + response)
            if "action" not in response:
                return response
            response = json.loads(response)
            actionResponse = ActionResponse(**response)
            match actionResponse.action:
                case "none":
                    if actionResponse.response:
                        return actionResponse.response
                case "more_info":
                    if actionResponse.response:
                        return actionResponse.response
                case "get_product_details":
                    if actionResponse.product_id and actionResponse.product_id != "":
                        product = await ProductService.get_product_by_id(actionResponse.product_id)
                        response = await LLMService.product_chat(product.dict(), actionResponse.user_query)
                        product_identifier = product_identifier_serializer(product.dict())
                        return {"related_products": [product_identifier], "message": response}
                    elif actionResponse.embedding_query and actionResponse.embedding_query != "":
                        embedding = await LLMService.create_embedding(actionResponse.embedding_query)
                        excludes = [
                            "_id",
                            "reviews",
                            "embedding",
                            "qa"
                        ]
                        documents, message = await LLMService.find_similar_embeddings(product_collection, embedding,
                                                                                      excludes,
                                                                                      actionResponse.embedding_query, 1)
                        if len(documents) == 0:
                            return ("No similar product found, we may not have that product in our database yet, "
                                    "try using the link feature to add it")
                        product = documents[0]
                        productCard = ProductCard(**product)
                        response = await LLMService.product_chat(product, actionResponse.user_query)
                        return {"products": [productCard], "message": response}
                case "find_similar":
                    if actionResponse.product_id and actionResponse.product_id != "":
                        product = await ProductService.get_product_by_id(actionResponse.product_id)
                        embedding = product.embedding
                        excludes = [
                            "_id",
                            "reviews",
                            "embedding",
                            "qa"
                        ]
                        documents, message = await LLMService.find_similar_embeddings(product_collection, embedding,
                                                                                      excludes,
                                                                                      actionResponse.embedding_query, 5)
                        if len(documents) == 0:
                            return ("No similar products found, we may not have that product in our database yet, "
                                    "try using the link feature to add it")
                        productCards = []
                        for product in documents:
                            productCards.append(ProductCard(**product.dict()))
                        return productCards
                    elif actionResponse.embedding_query and actionResponse.embedding_query != "":
                        embedding = await LLMService.create_embedding(actionResponse.embedding_query)
                        excludes = [
                            "_id",
                            "reviews",
                            "embedding",
                            "qa"
                        ]
                        documents, message = await LLMService.find_similar_embeddings(product_collection, embedding,
                                                                                      excludes,
                                                                                      actionResponse.embedding_query, 5)
                        if len(documents) == 0:
                            return ("No similar products found, we may not have that product in our database yet, "
                                    "try using the link feature to add it")

                        productCards = []
                        for product in documents:
                            productCards.append(ProductCard(**product))
                        return {"products": productCards, "message": message}
                case "compare_products":
                    if actionResponse.products and len(actionResponse.products) > 0:
                        if len(actionResponse.products) > 2:
                            return "You cannot compare more than 2 products at a time"
                        product1Id = actionResponse.products[0]["product_id"]
                        product2Id = actionResponse.products[1]["product_id"]
                        excludes = [
                            "_id",
                            "embedding",
                            "qa"
                        ]
                        product1 = None
                        product2 = None
                        if product1Id != "":
                            product1 = await ProductService.get_product_by_id(product1Id)
                            product1 = product1.dict()
                        else:
                            product1Name = actionResponse.products[0]["product_name"]
                            if product1Name != "":
                                product1_embedding = await LLMService.create_embedding(product1Name)
                                product1_documents, message = await LLMService.find_similar_embeddings(
                                    product_collection,
                                    product1_embedding,
                                    excludes, actionResponse.embedding_query, 1)
                                if len(product1_documents) == 0:
                                    return (
                                        "No similar product found, we may not have that product in our database yet, "
                                        "try using the link feature to add it")
                                product1 = product1_documents[0]

                        if product2Id != "":
                            product2 = await ProductService.get_product_by_id(product2Id)
                            product2 = product2.dict()
                        else:
                            product2Name = actionResponse.products[1]["product_name"]
                            product2_embedding = await LLMService.create_embedding(product2Name)

                            product2_documents, message = await LLMService.find_similar_embeddings(product_collection,
                                                                                                   product2_embedding,
                                                                                                   excludes,
                                                                                                   actionResponse.embedding_query,
                                                                                                   1)
                            if len(product2_documents) == 0:
                                return ("No similar product found, we may not have that product in our database yet, "
                                        "try using the link feature to add it")
                            product2 = product2_documents[0]
                        response = await LLMService.compare_products(product1, product2, actionResponse.user_query)
                        product1Identifier = product_identifier_serializer(product1)
                        product2Identifier = product_identifier_serializer(product2)
                        return {"related_products": [product1Identifier, product2Identifier], "message": response}
                case "search":
                    if actionResponse.embedding_query and actionResponse.embedding_query != "":
                        embedding = await LLMService.create_embedding(actionResponse.embedding_query)
                        excludes = [
                            "_id",
                            "reviews",
                            "embedding",
                            "qa"
                        ]
                        documents, message = await LLMService.find_similar_embeddings(product_collection, embedding,
                                                                                      excludes,
                                                                                      actionResponse.embedding_query, 5)
                        if len(documents) == 0:
                            return ("No similar products found, we may not have that product in our database yet, "
                                    "try using the link feature to add it")
                        productCards = []
                        for product in documents:
                            productCards.append(ProductCard(**product))
                        return {"products": productCards, "message": message}

            return "I'm sorry, I don't understand that request"
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=500, detail="Error in get_action_from_llm")
