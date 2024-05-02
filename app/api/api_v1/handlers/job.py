import uuid
from typing import List

import aiohttp
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer
from app.core.config import settings, manager

from app.models.conversation_model import Conversation, Message
from app.models.job_model import Job
from app.schemas.job_schema import JobIn, JobOut, JobRequest, JobUpdate
from app.schemas.product_schema import ProductOut, ProductCard
from app.services.conversation_service import ConversationService
from app.services.job_service import JobService
from app.services.product_service import ProductService
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


# deprecated user the socket endpoint
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
            action="link",
            scraper_id="amazon",
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
        await ConversationService.update_conversation(user_id, user_conversation)
        return created_job

    except HTTPException as e:
        logger.error("Unable to create job", e)
        raise e
    except Exception as e:
        logger.error("Unable to create job", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to create job")


@job_router.get("/by-user/{user_id}", summary="Get jobs by user", response_model=List[JobOut] or HTTPException)
async def get_jobs_by_user(request: Request, user_id: str):
    return await JobService.get_jobs_by_user(user_id)


@job_router.get("/by-status/{status}", summary="Get jobs by status", response_model=List[JobOut] or HTTPException)
async def get_jobs_by_status(request: Request, status: str):
    return await JobService.get_jobs_by_status(status)
