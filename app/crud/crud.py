from sqlmodel import Session, select
from ..models.job import Job
from ..database.database import engine
from ..schemas import schemas


def create_job(job: schemas.JobCreate):
    with Session(engine) as session:
        job = Job(**job.dict())
        session.add(job)
        session.commit()
        session.refresh(job)
        return job


def get_job(job_id: str):
    with Session(engine) as session:
        statement = select(Job).where(Job.id == job_id)
        result = session.exec(statement)
        return result.one()


def update_job(job_id: str, job: schemas.JobUpdate):
    with Session(engine) as session:
        statement = select(Job).where(Job.id == job_id)
        result = session.exec(statement)
        db_job = result.one()
        for key, value in job.dict().items():
            setattr(db_job, key, value)
        session.add(db_job)
        session.commit()
        session.refresh(db_job)
        return db_job
