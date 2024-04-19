from pydantic import BaseModel, EmailStr
from typing import Optional


class ActionResponse(BaseModel):
    action: str
    response: Optional[str] = None
    user_query: Optional[str] = None
    embedding_query: Optional[str] = None
    product_id: Optional[str] = None
    products: Optional[list] = None
