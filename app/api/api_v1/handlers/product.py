import asyncio
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer

from app.models.product_model import Product
from app.services.product_service import ProductService
from app.schemas.product_schema import ProductOut
from app.services.llm_service import LLMService
from app.core.logger import logger
from app.core.config import db_client

product_router = APIRouter(dependencies=[Depends(HTTPBearer())])


@product_router.get("/", summary="Get all products", response_model=List[ProductOut] or HTTPException)
async def get_products(request: Request) -> List[Product]:
    return await ProductService.get_products()


@product_router.get("/{product_id}", summary="Get product by id", response_model=ProductOut or HTTPException)
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


@product_router.post("/embedding/search", summary="Search for similar products",
                     response_model=List[ProductOut] or HTTPException)
async def search_similar_products(request: Request, body: dict):
    try:
        query = body.get("query")
        if not query:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query not provided")
        embedding = await LLMService.create_embedding(query)
        product_collection = db_client["products"]
        excludes = [
            "embedding",
            "reviews",
            "qa"
        ]
        documents = await LLMService.find_similar_embeddings(product_collection, embedding, excludes)
        return list(documents)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error searching for similar products")


@product_router.post("/{product_id}/chat")
async def chat_with_product(request: Request, product_id: str, body: dict):
    try:
        query = body.get("query")
        product = await ProductService.get_product_by_id(product_id)
        product_dict = product.json()
        return LLMService.product_chat(product_dict, query)
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
