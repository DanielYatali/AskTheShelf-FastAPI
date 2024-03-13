from pydantic import BaseModel


class Job(BaseModel):
    id: str
    status: str
    start_time: str
    end_time: str
    result: dict
    error: dict
