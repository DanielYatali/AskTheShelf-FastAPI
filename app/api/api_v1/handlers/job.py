import asyncio
import subprocess
import uuid
from datetime import datetime
from typing import List

import aiohttp
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer
from app.core.config import settings

from app.models.conversation_model import Conversation, Message
from app.models.job_model import Job
from app.models.product_model import Product
from app.schemas.job_schema import JobIn, JobOut, JobRequest, JobUpdate
from app.schemas.product_schema import ProductOut, ProductCard
from app.services.conversation_service import ConversationService
from app.services.job_service import JobService
from app.services.product_service import ProductService
from app.services.llm_service import LLMService
from app.core.logger import logger
from app.utils.utils import extract_asin_from_url

job_router = APIRouter(dependencies=[Depends(HTTPBearer())])


@job_router.get("/", summary="Get all jobs", response_model=List[JobOut] or HTTPException)
async def get_jobs(request: Request) -> List[JobOut]:
    return await JobService.get_jobs()


@job_router.get("/{job_id}", summary="Get job by id", response_model=JobOut or HTTPException)
async def get_job(request: Request, job_id: str):
    try:
        job = await JobService.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        return job
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@job_router.post("/", summary="Create job")
async def create_job(request: Request, job: JobRequest):
    try:
        if "amazon" not in job.url:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a valid amazon url")
        asin = extract_asin_from_url(job.url)

        if not asin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a valid amazon url")
        clean_url = f"https://www.amazon.com/dp/{asin}"
        user = request.state.user
        user_id = user.user_id
        user_conversation = await ConversationService.get_conversation_by_user_id(user_id)
        if not user_conversation:
            conversation = Conversation(user_id=user_id, messages=[])
            user_conversation = await ConversationService.create_conversation(conversation)
        user_message = Message(
            role="user",
            content=clean_url,
        )
        user_conversation.messages.append(user_message)
        product = await ProductService.get_product_by_id(asin)
        if product is not None:
            productOut = ProductCard(**product.dict())
            assistant_message = Message(
                role="assistant",
                content="Here is the product you requested",
                products=[productOut],
            )
            user_conversation.messages.append(assistant_message)
            await ConversationService.update_conversation(user_id, user_conversation)
            return {"message": "Here is the product you requested", "products": [productOut]}

        new_job = Job(
            job_id=str(uuid.uuid4()),
            user_id=request.state.user.user_id,
            url=clean_url,
            product_id=asin,
        )
        created_job = await JobService.create_job(new_job)
        scraper_url = settings.SCRAPER_URL
        if not scraper_url:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Scraper URL not found")
        scraper_url += "/schedule.json"
        # Asynchronous POST request using aiohttp
        data = {
            "project": "default",
            "spider": "amazon",
            "job_id": new_job.job_id,
            "url": new_job.url,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(scraper_url, data=data) as response:
                if response.status != 200:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to post job to scraper")
        # command = ["scrapy", "crawl", "amazon", "-a", f"url={new_job.url}", "-a", f"job_id={new_job.job_id}"]
        # subprocess.Popen(command, cwd="scrapy-project")
        await ConversationService.update_conversation(user_id, user_conversation)
        return created_job

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to create job")


@job_router.put("/jobs", summary="Update job")
async def update_job(job: dict):
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
        await JobService.delete_job(job_id)
        return {
            "status": "success",
        }

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job not found")


@job_router.get("/by-user/{user_id}", summary="Get jobs by user", response_model=List[JobOut] or HTTPException)
async def get_jobs_by_user(request: Request, user_id: str):
    return await JobService.get_jobs_by_user(user_id)


@job_router.get("/by-status/{status}", summary="Get jobs by status", response_model=List[JobOut] or HTTPException)
async def get_jobs_by_status(request: Request, status: str):
    return await JobService.get_jobs_by_status(status)
