from pydantic import BaseModel
from typing import Optional
from pydantic import Field


class Product(BaseModel):
    id: str
    job_id: str
    domain: str
    title: str
    description: str
    price: float
    image_url: str
    specs: dict
    features: list
    reviews: list
    rating: float
    created_at: str
    updated_at: str
    similar_products: Optional[list] = []
    generated_review: Optional[str] = ""







