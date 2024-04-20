from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProductValidateSearch(BaseModel):
    product_id: str
    embedding_text: str


def product_identifier_serializer(product):
    return {
        "product_id": product["product_id"],
        "product_name": product["title"],
        "domain": product["domain"]
    }


class ProductCard(BaseModel):
    product_id: str
    title: str
    image_url: str
    price: float
    rating: Optional[float] = 0.0
    domain: str
    affiliate_url: Optional[str] = ""


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
    affiliate_url: Optional[str] = ""


class ProductForUser(BaseModel):
    product_id: str
    domain: str
    title: str
    description: str
    price: float
    image_url: str
    rating: float
    specs: dict
    features: list
    created_at: datetime
    updated_at: datetime
    variants: Optional[dict] = {}
    number_of_reviews: Optional[str] = ""
    generated_review: Optional[str] = ""
    affiliate_url: Optional[str] = ""
