from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from beanie import Document, Indexed
from typing import Optional


class Product(Document):
    product_id: Indexed(str, unique=True)
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
    embedding: Optional[list] = []
    embedding_text: Optional[str] = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    similar_products: Optional[list] = []
    variants: Optional[dict] = {}
    number_of_reviews: Optional[str] = ""
    qa: Optional[list] = []
    generated_review: Optional[str] = ""

    def __repr__(self) -> str:
        return f'<Product {self.product_id}>'

    def __str__(self) -> str:
        return self.product_id

    def __hash__(self) -> int:
        return hash(self.product_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Product):
            return False
        return self.product_id == other.product_id

    @property
    def create(self) -> datetime:
        return self.id.generation_time

    @classmethod
    async def by_id(self, product_id: str) -> "Product":
        return await self.find_one(self.product_id == product_id)

    @classmethod
    async def by_job_id(self, job_id: str) -> "Product":
        return await self.find_one(self.job_id == job_id)

    class Settings:
        name = "products"
