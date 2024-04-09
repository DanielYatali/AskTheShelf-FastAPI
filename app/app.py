from fastapi import FastAPI, Depends, HTTPException, status, Security
from app.core.config import settings
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from app.models.user_model import User
from app.models.job_model import Job
from app.models.product_model import Product
from app.api.api_v1.router import router
from app.core.logger import logger
from app.core.middlewares import AuthMiddleware
from app.core.config import init_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=None,
)


@app.on_event("startup")
async def app_startup():
    await init_db()


app.include_router(router)
app.add_middleware(AuthMiddleware, allow_routes=["/users", "/api/v1/docs", "/api/v1/openapi.json", "/robots.txt",
                                                 "/api/v1/scrapy/update"])
