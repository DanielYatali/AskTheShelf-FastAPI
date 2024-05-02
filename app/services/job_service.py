import json
import uuid
from typing import Optional

import aiohttp
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.logger import logger
from app.models.conversation_model import Message, Conversation
from app.models.job_model import Job
from app.schemas.job_schema import JobUpdate
from app.schemas.llm_schema import ActionResponse
from app.schemas.product_schema import ProductCard
from app.services.conversation_service import ConversationService
from app.services.product_service import ProductService
from app.utils.utils import extract_asin_from_url


class JobService:
    @staticmethod
    async def create_job(job: Job) -> Optional[Job]:
        await job.save()
        return job

    @staticmethod
    async def get_job_by_id(job_id: str) -> Optional[Job]:
        job = await Job.find_one(Job.job_id == job_id)
        if not job:
            return None
        return job

    @staticmethod
    async def get_jobs():
        jobs = await Job.all().to_list()
        return jobs

    @staticmethod
    async def get_jobs_by_user(user_id: str):
        jobs = await Job.find(Job.user_id == user_id).to_list()
        return jobs

    @staticmethod
    async def get_jobs_by_status(status: str):
        jobs = await Job.find(Job.status == status).to_list()
        return jobs

    @staticmethod
    async def update_job(job_id: str, job: JobUpdate) -> Optional[Job]:
        existing_job = await Job.find_one(Job.job_id == job_id)
        if not existing_job:
            return None
        existing_job.status = job.status
        existing_job.result = job.result
        existing_job.error = job.error
        existing_job.end_time = job.end_time
        await existing_job.save()
        return existing_job

    @staticmethod
    async def delete_job(job_id: str) -> Optional[Job]:
        job = await Job.find_one(Job.job_id == job_id)
        if not job:
            return None
        await job.delete()
        return job

    @staticmethod
    async def search_amazon_products(query: str, user_id: str, user_query: str):
        url = f"https://www.amazon.com/s?k={query}"
        new_job = Job(
            job_id=str(uuid.uuid4()),
            query=query,
            user_id=user_id,
            action="search",
            user_query=user_query,
            scraper_id="amazon_search",
            url=url,
        )
        created_job = await JobService.create_job(new_job)
        scraper_url = settings.SCRAPER_URL
        if not scraper_url:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Scraper URL not found")
        scraper_url += "/schedule.json"
        # Asynchronous POST request using aiohttp
        data = {
            "project": "default",
            "spider": "amazon_search",
            "job_id": new_job.job_id,
            "url": new_job.url,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(scraper_url, data=data) as response:
                if response.status != 200:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to post job to scraper")

        return created_job

    @staticmethod
    async def get_product_details(user_id: str, action: ActionResponse, urls: list):
        new_job = Job(
            job_id=str(uuid.uuid4()),
            user_id=user_id,
            action=action.action,
            user_query=action.user_query,
            scraper_id="amazon_get_details",
            url=json.dumps(urls),
        )
        created_job = await JobService.create_job(new_job)
        scraper_url = settings.SCRAPER_URL
        if not scraper_url:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Scraper URL not found")
        scraper_url += "/schedule.json"
        # Asynchronous POST request using aiohttp
        data = {
            "project": "default",
            "spider": "amazon_get_details",
            "job_id": new_job.job_id,
            "url": urls
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(scraper_url, data=data) as response:
                if response.status != 200:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to post job to scraper")

        return created_job

    @staticmethod
    async def basic_get_products(user_id: str, action: ActionResponse, urls: list):
        new_job = Job(
            job_id=str(uuid.uuid4()),
            user_id=user_id,
            action=action.action,
            user_query=action.user_query,
            scraper_id="amazon_get_details",
            url=json.dumps(urls),
        )
        created_job = await JobService.create_job(new_job)
        scraper_url = settings.SCRAPER_URL
        if not scraper_url:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Scraper URL not found")
        scraper_url += "/schedule.json"
        # Asynchronous POST request using aiohttp
        data = {
            "project": "default",
            "spider": "amazon_get_details",
            "job_id": new_job.job_id,
            "url": json.dumps(urls)
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(scraper_url, data=data) as response:
                if response.status != 200:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to post job to scraper")

        return created_job

    # TODO: Refactor this method
    @staticmethod
    async def get_comprehensive_product_details(user_id: str, url: str):
        try:
            if "amazon" not in url:
                assistant_message = Message(
                    role="assistant",
                    content="Not a valid amazon url",
                )
                return assistant_message
            asin = extract_asin_from_url(url)
            if not asin:
                assistant_message = Message(
                    role="assistant",
                    content="Not a valid amazon url",
                )
                return assistant_message
            clean_url = f"https://www.amazon.com/dp/{asin}"
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
                return assistant_message
            new_job = Job(
                job_id=str(uuid.uuid4()),
                user_id=user_id,
                url=clean_url,
                action="link",
                scraper_id="amazon",
            )
            created_job = await JobService.create_job(new_job)
            scraper_url = settings.SCRAPER_URL
            if not scraper_url:
                logger.error("Scraper URL not found")
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
                        logger.error("Failed to post job to scraper")
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                            detail="Failed to post job to scraper")
            assistant_message = Message(
                role="assistant",
                content="We are fetching the product details for you, please wait",
            )
            user_conversation.messages.append(assistant_message)
            await ConversationService.update_conversation(user_id, user_conversation)
            return assistant_message

        except Exception as e:
            logger.error("Unable to create job", e)
            assistant_message = Message(
                role="assistant",
                content="Failed to get product details, please try again",
            )
            return assistant_message
