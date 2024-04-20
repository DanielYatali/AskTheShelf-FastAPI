from fastapi import FastAPI, Depends, HTTPException, status, Security
from starlette.middleware.cors import CORSMiddleware

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
allowed_origins = [
    "http://localhost:3000",  # Assuming your frontend runs on localhost:3000
    "https://example.com",  # Replace with your actual domain
]


@app.on_event("startup")
async def app_startup():
    await init_db()


app.include_router(router)
# Add CORSMiddleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # List of allowed origins
    allow_credentials=True,  # Allow cookies to be included in cross-origin requests
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)
app.add_middleware(AuthMiddleware, allow_routes=["/users", "/api/v1/docs", "/api/v1/openapi.json", "/robots.txt",
                                                 "/api/v1/scrapy/update"])

