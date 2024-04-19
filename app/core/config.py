from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseSettings
from decouple import config
from typing import List
from pydantic import AnyHttpUrl
from app.core.logger import logger
from app.models.job_model import Job
from app.models.product_model import Product
from app.models.user_model import User
from app.models.product_error_model import ProductError
from app.models.conversation_model import Conversation


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    JWT_SECRET_KEY: str = config('JWT_SECRET_KEY', cast=str)
    AUTH0_AUDIENCE: str = config('AUTH0_AUDIENCE', cast=str)
    AUTH0_DOMAIN: str = config('AUTH0_DOMAIN', cast=str)
    AUTH0_CLIENT_ID: str = config('AUTH0_CLIENT_ID', cast=str)
    AUTH0_CLIENT_SECRET: str = config('AUTH0_CLIENT_SECRET', cast=str)
    AUTH0_ALGORITHMS: str = config('AUTH0_ALGORITHMS', cast=str)
    AUTH0_ISSUER: str = f"https://{AUTH0_DOMAIN}/"
    JWT_REFRESH_SECRET_KEY: str = config('JWT_REFRESH_SECRET_KEY', cast=str)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    OPENAI_API_KEY: str = config('OPENAI_API_KEY', cast=str)
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    PROJECT_NAME: str = "Amazon Scraper"
    MONGODB_CONNECTION_STRING: str = config('MONGODB_CONNECTION_STRING', cast=str)
    BASE_URL: str = config('BASE_URL', cast=str)

    class Config:
        case_sensitive = True


settings = Settings()

async def init_db():
    # Initiate connection to MongoDB
    logger.info("Connecting to MongoDB")
    db_client = AsyncIOMotorClient(settings.MONGODB_CONNECTION_STRING).scraper
    # Assuming init_beanie is a function that needs to be called at app startup
    await init_beanie(
        database=db_client,
        document_models=[
            User,  # Ensure User is imported
            Job,  # Ensure Job is imported
            Product,  # Ensure Product is imported
            ProductError,
            Conversation
        ],
    )
    logger.info("Connected to MongoDB")
