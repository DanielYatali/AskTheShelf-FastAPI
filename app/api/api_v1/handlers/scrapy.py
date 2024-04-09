import asyncio
import subprocess
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer

from app.models.job_model import Job
from app.models.product_model import Product
from app.schemas.job_schema import JobIn, JobOut, JobRequest, JobUpdate
from app.schemas.product_schema import ProductOut
from app.services.job_service import JobService
from app.services.product_service import ProductService
from app.services.llm_service import LLMService
from app.core.logger import logger
from app.utils.utils import extract_asin_from_url

scrapy_router = APIRouter()


@scrapy_router.post("/update", summary="Update job")
async def update_job(request: Request, job: dict):
    try:
        job_id = job["job_id"]
        job = JobUpdate(**job)
        updated_job = await JobService.update_job(job_id, job)
        if not updated_job:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job not found")
        product_data = updated_job.result
        if not product_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No product data found in job")
        product_id = product_data["product_id"]
        existing_product = await ProductService.get_product_by_id(product_id)
        if existing_product:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product already exists")
        new_product = Product(**product_data)
        new_product.user_id = updated_job.user_id
        new_product = await ProductService.create_product(new_product)
        generated_review, embedding_text = await asyncio.gather(
            LLMService.generate_product_review(product_data),
            LLMService.generate_embedding_text(product_data)
        )
        embedding = await LLMService.create_embedding(embedding_text)
        new_product.generated_review = generated_review
        new_product.embedding = embedding
        new_product.embedding_text = embedding_text
        new_product.updated_at = datetime.now()
        await ProductService.update_product(product_id, new_product)
        return {
            "status": "success",
        }

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job not found")
