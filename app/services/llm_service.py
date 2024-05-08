import json
from dataclasses import dataclass
from typing import List, Optional, Union, Dict

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

from app.utils.utils import parse_json

GPT3 = "gpt-3.5-turbo"
OPEN_AI_EMBEDDING = "text-embedding-ada-002"
GEMINI = "gemini-pro"
# Tried llama it did a terrible job with json
Llama = "Llama3-8b-8192"
GEMINI_EMBEDDING = "text-embedding-004"


@dataclass
class RequestContext:
    conversation: Conversation
    model: str
    user_query: str
    action: Optional[ActionResponse] = None


class LLMService:
    @staticmethod
    async def find_similar_products(request_context: RequestContext, limit: int):
        # Build the pipeline for vector search
        collection = Product.get_motor_collection()
        action = request_context.action
        conversation = request_context.conversation
        query = action.embedding_query
        model = request_context.model
        excludes = [
            "_id",
            "embedding",
            "similar_products",
            "user_id",
        ]
        if not limit:
            limit = 1
        embedding = await LLMService.create_embedding(action.embedding_query, model)
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
                response = await LLMService.validate_embedding_search(products, conversation, query, model)
                response_data = parse_json(response)
                if not response_data:
                    logger.error("Bad response from LLM")
                    response = await LLMService.validate_embedding_search(products, conversation, query, model)
                    response_data = parse_json(response)
                    if not response_data:
                        return [], "Bad response from LLM"
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

    @staticmethod
    async def validate_embedding_search(products: list[ProductValidateSearch], conversation: Conversation, query: str,
                                        model=None):
        async with aiofiles.open('prompts/validate_embedding_search_prompt.txt', mode='r') as file:
            prompt = await file.read()

        context = conversation.messages[-11:]
        # remove the last message which is the user query
        context.pop()
        json_context = [item.json() for item in context]
        prompt = prompt.replace("{{conversation}}", json.dumps(json_context))
        prompt = prompt.replace("{{products}}", json.dumps([product.dict() for product in products]))
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": query}
        ]
        return await LLMService.llm_request(messages, model)

    @staticmethod
    async def create_open_ai_embedding(query, model=None):
        # try:
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
    async def create_embedding(query, model=None):
        # try:
        # if model is None:
        #     model = OPEN_AI_EMBEDDING
        # if model == OPEN_AI_EMBEDDING:
        return await LLMService.create_open_ai_embedding(query, model)
        # elif model == GEMINI_EMBEDDING:
        #     return await LLMService.create_gemini_embedding(query, model)

    @staticmethod
    async def generate_product_review(product):
        # try:
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

    @staticmethod
    async def generate_embedding_text(product, model):
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

    @staticmethod
    async def product_chat(product: Dict, action: ActionResponse, request_context: RequestContext, model: str) -> str:
        async with aiofiles.open('prompts/product_chat_prompt.txt', mode='r') as file:
            prompt = await file.read()
        conversation = request_context.conversation
        query = action.user_query
        product.pop("embedding", None)
        product.pop("similar_products", None)
        product.pop("embedding_text", None)

        context = conversation.messages[-11:]
        # remove the last message which is the user query
        context.pop()
        json_context = [item.json() for item in context]
        prompt = prompt.replace("{{conversation}}", json.dumps(json_context))
        prompt = prompt.replace("{{product}}", json.dumps(product))
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": query}
        ]
        response = await LLMService.llm_request(messages, model)
        return response

    @staticmethod
    async def make_llm_request(conversation):
        # try:
        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation
        )
        message = completion.choices[0].message.model_dump()
        return message["content"]

    @staticmethod
    async def make_openai_request(conversation, model=GPT3):
        # try:
        client = OpenAI()
        completion = client.chat.completions.create(
            model=model,
            messages=conversation,
            temperature=0
        )
        message = completion.choices[0].message.model_dump()
        return message["content"]

    @staticmethod
    async def make_gemini_request(conversation, model=GEMINI):
        # try:
        generation_config = genai.GenerationConfig(
            candidate_count=1,
            temperature=0,
        )
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(model, generation_config=generation_config)
        response = await model.generate_content_async(json.dumps(conversation))
        return response.text

    @staticmethod
    async def make_groq_request(conversation, model=Llama):
        client = Groq(
            api_key=settings.GROQ_API_KEY,
        )
        chat_completion = client.chat.completions.create(
            messages=conversation,
            model=model
        )
        return chat_completion.choices[0].message.content

    @staticmethod
    async def create_gemini_embedding(query, model=GEMINI_EMBEDDING):
        # try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        result = genai.embed_content(
            model="models/" + model,
            content=query,
            task_type="retrieval_document",
            title="Embedding of list of strings")
        return result.get("embedding", [])

    @staticmethod
    async def llm_request(conversation, model=GPT3):
        if model == GPT3:
            return await LLMService.make_openai_request(conversation, GPT3)
        elif model == GEMINI:
            return await LLMService.make_gemini_request(conversation, GEMINI)
        elif model == Llama:
            return await LLMService.make_groq_request(conversation, Llama)
        return await LLMService.make_openai_request(conversation, GPT3)

    @staticmethod
    async def compare(product1, product2, user_query, model):
        async with aiofiles.open('prompts/compare_products_prompt.txt', mode='r') as file:
            prompt = await file.read()
        product1.pop("embedding", None)
        product1.pop("embedding_text", None)
        product2.pop("embedding", None)
        product2.pop("embedding_text", None)
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user",
             "content": f"{product1}"},
            {"role": "user",
             "content": f"{product2}"},
            {"role": "user", "content": user_query}
        ]
        return await LLMService.llm_request(messages, model)

    @staticmethod
    async def manager(query, conversation: Conversation, model):
        async with aiofiles.open('prompts/manager.txt', mode='r') as file:
            prompt = await file.read()
        # context is an array of Message objects
        context = conversation.messages[-11:]
        context.pop()
        json_context = [item.json() for item in context]

        prompt = prompt.replace("{{conversation}}", json.dumps(json_context))
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": query}
        ]
        response = await LLMService.llm_request(messages, model)
        if "action" not in response:
            logger.info("LLM did not return an action, trying again")
            messages.append({"role": "system", "content": response})
            messages.append({"role": "user", "content": "You did not return an action, please try again"})
            response = await LLMService.llm_request(messages, model)
        if "action" in response:
            response = parse_json(response)
            if not response:
                messages.append({"role": "system", "content": response})
                messages.append({"role": "user", "content": "Invalid JSON response please try again"})
                response = await LLMService.llm_request(messages, model)
                logger.info("Corrected response from LLM:" + response)
            else:
                return response
        try:
            response = parse_json(response)
        except json.JSONDecodeError as e:
            logger.info("Invalid JSON response from LLM", str(e))
            return
        return response

    @staticmethod
    async def find_product_by_name(request_context: RequestContext, product_name) -> Union[Product, None]:
        request_context.conversation.messages = []
        request_context.action.embedding_query = product_name
        documents, message = await LLMService.find_similar_products(request_context, 1)
        if len(documents) == 0:
            return None
        return documents[0]

    @staticmethod
    async def find_similar(request_context: RequestContext) -> Message:
        action = request_context.action

        if LLMService.is_valid_product(action):
            product_id = action.products[0]["product_id"]
            product = await ProductService.get_product_by_id(product_id)
            action.embedding_query = product.embedding_text

            return await LLMService.process_similarity_search(request_context, 10)

        if action.embedding_query:
            return await LLMService.process_similarity_search(request_context, 10)

        return Message(
            role="assistant",
            content="Encounter an error while processing the request, please try again."
        )

    @staticmethod
    def is_valid_product(action):
        return action.products and len(action.products) > 0 and action.products[0].get("product_id")

    @staticmethod
    async def process_similarity_search(request_context, limit) -> Message:
        action = request_context.action
        conversation = request_context.conversation
        documents, message = await LLMService.find_similar_products(request_context, limit)
        if not documents:
            response = await LLMService.handle_no_documents_found(action, conversation)
            return Message(
                role="assistant",
                content=response
            )

        product_cards = [ProductCard(**product) for product in documents]
        return Message(
            role="assistant",
            content=message,
            products=product_cards
        )

    @staticmethod
    async def handle_no_documents_found(action, conversation):
        if action.embedding_query:
            job = await JobService.search_amazon_products(action.embedding_query, conversation.user_id,
                                                          action.user_query)
            if job:
                return "No similar products found in our database, we are searching Amazon for you, please wait..."
        return "No similar products found, we may not have that product in our database yet"

    @staticmethod
    async def get_product_details(request_context: RequestContext) -> Message:
        action = request_context.action
        model = request_context.model
        if LLMService.is_valid_product(action):
            product = await LLMService.get_product_from_action(request_context, action.products[0])
            if product is None:
                return Message(
                    role="assistant",
                    content="Product details not found, if a search on amazon was previously initiated, we may still "
                            "be gathering the details, please wait..., if issue persists, please try again later."
                )
            response = await LLMService.product_chat(product.dict(), action, request_context, model)
            product_identifier = product_identifier_serializer(product.dict())
            return Message(
                role="assistant",
                content=response,
                related_products=[product_identifier]
            )
        elif action.embedding_query and action.embedding_query != "":
            documents, message = await LLMService.find_similar_products(request_context, 1)
            if len(documents) == 0:
                return Message(
                    role="assistant",
                    content="No similar product found, we may not have that product in our database yet, "
                            "try using the link feature to add it"
                )
            product = documents[0]
            productCard = ProductCard(**product)
            response = await LLMService.product_chat(product, action, request_context, model)
            return Message(
                role="assistant",
                content=response,
                products=[productCard]
            )

    @staticmethod
    async def get_product_from_action(request_context, action_product) -> Union[Product, None]:
        product_id = action_product.get("product_id", "")
        if product_id:
            product = await ProductService.get_product_by_id(product_id)
            if product:
                return product
            return None
        product_name = action_product.get("product_name", "")
        if product_name:
            return await LLMService.find_product_by_name(request_context=request_context, product_name=product_name)
        return None

    @staticmethod
    async def compare_products(request_context: RequestContext) -> Message:
        action = request_context.action
        if not action.products or len(action.products) != 2:
            message = Message(
                role="assistant",
                content="Please provide two products to compare"
            )
            return message
        product1 = await LLMService.get_product_from_action(request_context, action.products[0])
        product2 = await LLMService.get_product_from_action(request_context, action.products[1])
        if not product1 or not product2:
            message = Message(
                role="assistant",
                content="One or both products were not found in the database, try using the link feature to add them "
                        "or search Amazon."
            )
            return message
        product1 = product1.dict()
        product2 = product2.dict()
        response = await LLMService.compare(product1, product2, action.user_query, request_context.model)
        product1_identifier = product_identifier_serializer(product1)
        product2_identifier = product_identifier_serializer(product2)
        message = Message(
            role="assistant",
            content=response,
            related_products=[product1_identifier, product2_identifier]
        )
        return message

    # TODO: Refactor this to return a Message object
    @staticmethod
    async def get_action_from_llm(query, conversation: Conversation, model) -> Message:
        response = await LLMService.manager(query, conversation, model)
        if "action" not in response:
            return response
        action = ActionResponse(**response)
        request_context = RequestContext(action=action, conversation=conversation, model=model,
                                         user_query=query)
        match action.action:
            case "none":
                logger.info("In none case")
                if action.response:
                    return Message(
                        role="assistant",
                        content=action.response
                    )
            case "more_info":
                logger.info("In more_info case")
                if action.response:
                    return Message(
                        role="assistant",
                        content=action.response
                    )
            case "get_product_details":
                logger.info("In get_product_details case")
                return await LLMService.get_product_details(request_context)
            case "find_similar":
                logger.info("In find_similar case")
                return await LLMService.find_similar(request_context)
            case "compare_products":
                logger.info("In compare_products case")
                return await LLMService.compare_products(request_context)
            case "search":
                logger.info("In search case")
                if action.embedding_query and action.embedding_query != "":
                    return await LLMService.process_similarity_search(request_context, 10)
            case "search_amazon":
                logger.info("In search_amazon case")
                job = await JobService.search_amazon_products(action.embedding_query, conversation.user_id, query)
                if job:
                    return Message(
                        role="assistant",
                        content="Searching Amazon for you, please wait..."
                    )
        return Message(
            role="assistant",
            content="I'm sorry, I encountered an error while processing your request"
        )
