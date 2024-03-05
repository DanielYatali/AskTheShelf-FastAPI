from pydantic import BaseModel
from datetime import datetime


class Job(BaseModel):
    id: str
    status: str
    start_time: str
    end_time: str
    result: str
    error: str


class JobCreate(BaseModel):
    id: str
    url: str
    status: str
    start_time: datetime


class Product(BaseModel):
    id: str
    title: str
    image_url: str
    url: str
    description: str
    specs: dict
    price: str
    features: list
    reviews: list


class JobUpdate(BaseModel):
    id: str
    status: str
    end_time: datetime
    result: Product
    error: str


