from datetime import datetime

from beanie import Document, Indexed
from typing import Optional

from pydantic import Field


class ProductError(Document):
    product_id: Indexed(str, unique=True)
    job_id: str
    user_id: Optional[str] = ""
    error: Optional[list] = []
    created_at: datetime = Field(default_factory=datetime.now)

    def __repr__(self) -> str:
        return f'<ProductError {self.product_id}>'

    def __str__(self) -> str:
        return self.product_id

    class Settings:
        name = "product_errors"
