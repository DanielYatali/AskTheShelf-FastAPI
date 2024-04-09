from typing import Optional

from app.models.job_model import Job
from app.schemas.job_schema import JobUpdate


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
