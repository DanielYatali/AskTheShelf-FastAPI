from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProductSchema(BaseModel):
    product_id: str
    user_id: Optional[str] = ""
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
    variants: Optional[dict] = {}
    number_of_reviews: Optional[str] = ""
    qa: Optional[list] = []
    generated_review: Optional[str] = ""


class ProductOut(BaseModel):
    product_id: str
    job_id: str
    user_id: Optional[str] = ""
    domain: str
    title: str
    description: str
    price: float
    image_url: str
    specs: dict
    features: list
    reviews: list
    rating: float
    created_at: datetime
    updated_at: datetime
    similar_products: Optional[list] = []
    variants: Optional[dict] = {}
    number_of_reviews: Optional[str] = ""
    qa: Optional[list] = []
    generated_review: Optional[str] = ""
