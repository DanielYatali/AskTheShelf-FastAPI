import asyncio
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer

from app.models.conversation_model import Conversation, Message
from app.models.product_error_model import ProductError
from app.models.product_model import Product
from app.services.conversation_service import ConversationService
from app.services.product_service import ProductService, ProductErrorService
from app.schemas.product_schema import ProductOut, ProductForUser
from app.services.llm_service import LLMService
from app.core.logger import logger
from app.config.database import product_collection

product_router = APIRouter(dependencies=[Depends(HTTPBearer())])


@product_router.get("/", summary="Get all products", response_model=List[ProductOut] or HTTPException)
async def get_products(request: Request) -> List[Product]:
    return await ProductService.get_products()


@product_router.get("/errors", summary="Get all product errors", response_model=List[ProductError] or HTTPException)
async def get_product_errors(request: Request):
    print("get_product_errors")
    return await ProductErrorService.get_product_errors()


@product_router.get("/{product_id}", summary="Get product by id", response_model=ProductForUser or HTTPException)
async def get_product(request: Request, product_id: str):
    try:
        product = await ProductService.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@product_router.get("/{product_id}/card", summary="Get product by id", response_model=ProductForUser or HTTPException)
async def get_product(request: Request, product_id: str):
    try:
        product = await ProductService.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@product_router.post("/", summary="Create product", response_model=Product or HTTPException)
async def create_product(request: Request, product: Product):
    try:
        return await ProductService.create_product(product)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product already exists")


@product_router.post("/embedding/search", summary="Search for similar products")
async def search_similar_products(request: Request, body: dict):
    try:
        query = body.get("query")
        if not query:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query not provided")
        embedding = await LLMService.create_embedding(query)
        excludes = [
            "_id",
            "embedding",
            "reviews",
            "qa"
        ]
        documents, message = await LLMService.find_similar_embeddings(product_collection, embedding, excludes, query, 5)
        return documents
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error searching for similar products")


@product_router.post("/{product_id}/chat")
async def chat_with_product(request: Request, product_id: str, body: dict):
    try:
        query = body.get("query")
        product = await ProductService.get_product_by_id(product_id)
        product_dict = product.dict()
        return await LLMService.product_chat(product_dict, query)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="Product not found")


@product_router.put("/{product_id}", summary="Update product", response_model=Product or HTTPException)
async def update_product(request: Request, product_id: str, product: Product):
    try:
        return await ProductService.update_product(product_id, product)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found")


@product_router.put("/{product_id}/regenerate", summary="Regenerate product", response_model=Product or HTTPException)
async def regenerate_product(request: Request, product_id: str):
    try:
        product = await ProductService.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        generated_review, embedding_text = await asyncio.gather(
            LLMService.generate_product_review(product),
            LLMService.generate_embedding_text(product)
        )
        embedding = await LLMService.create_embedding(embedding_text)
        product.generated_review = generated_review
        product.embedding = embedding
        product.embedding_text = embedding_text
        product.updated_at = datetime.now()
        return await ProductService.update_product(product_id, product)

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found")


@product_router.delete("/{product_id}", summary="Delete product", response_model=ProductOut or HTTPException)
async def delete_product(request: Request, product_id: str):
    try:
        return await ProductService.delete_product(product_id)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found")


@product_router.post("/chat", summary="Chat with LLM")
async def chat_with_llm(request: Request, body: dict):
    try:
        query = body.get("query")
        if not query:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query not provided")
        user = request.state.user
        user_id = user.user_id
        user_conversation = await ConversationService.get_conversation_by_user_id(user_id)
        if not user_conversation:
            conversation = Conversation(user_id=user_id, messages=[])
            user_conversation = await ConversationService.create_conversation(conversation)
        user_message = Message(
            role="user",
            content=query,
        )
        response = await LLMService.get_action_from_llm(query, user_conversation)
        user_conversation.messages.append(user_message)
        if isinstance(response, dict):
            if 'products' in response:
                assistant_message = Message(
                    role="assistant",
                    content=response['message'],
                    products=response['products'],
                )
                user_conversation.messages.append(assistant_message)
                await ConversationService.update_conversation(user_id, user_conversation)
                return assistant_message
            else:
                assistant_message = Message(
                    role="assistant",
                    content=response['message'],
                    related_products=response['related_products'],
                )
                user_conversation.messages.append(assistant_message)
                user_conversation.messages.append(assistant_message)
                await ConversationService.update_conversation(user_id, user_conversation)
                return assistant_message
        else:
            assistant_message = Message(
                role="assistant",
                content=response,
            )
            user_conversation.messages.append(assistant_message)
            await ConversationService.update_conversation(user_id, user_conversation)
            return assistant_message

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="Error chatting with LLM")
