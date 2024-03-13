from pydantic import BaseModel


class Product(BaseModel):
    id: str
    job_id: str
    product_id: str
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
    generated_review: str






