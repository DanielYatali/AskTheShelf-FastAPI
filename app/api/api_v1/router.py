from fastapi import APIRouter
from app.api.api_v1.handlers import user
from app.api.api_v1.handlers import job
from app.api.api_v1.handlers import product
from app.api.api_v1.handlers import conversation
from app.api.api_v1.handlers import scrapy
from app.core.config import settings

router = APIRouter()
router.include_router(user.user_router, prefix=settings.API_V1_STR + "/users", tags=["users"])
router.include_router(job.job_router, prefix=settings.API_V1_STR + "/jobs", tags=["jobs"])
router.include_router(product.product_router, prefix=settings.API_V1_STR + "/products", tags=["products"])
router.include_router(scrapy.scrapy_router, prefix=settings.API_V1_STR + "/scrapy", tags=["scrapy"])
router.include_router(conversation.conversation_router, prefix=settings.API_V1_STR + "/conversations", tags=["conversations"])

