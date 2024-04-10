from beanie import Document, Indexed
from typing import Optional


class ProductError(Document):
    product_id: Indexed(str, unique=True)
    job_id: str
    user_id: Optional[str] = ""
    error: Optional[list] = []

    def __repr__(self) -> str:
        return f'<ProductError {self.product_id}>'

    def __str__(self) -> str:
        return self.product_id

    class Settings:
        name = "product_errors"
