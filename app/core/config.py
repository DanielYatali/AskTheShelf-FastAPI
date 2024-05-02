from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseSettings
from decouple import config
from typing import List, Dict
from pydantic import AnyHttpUrl
from app.core.logger import logger
from app.models.job_model import Job
from app.models.product_model import Product
from app.models.user_model import User
from app.models.product_error_model import ProductError
from app.models.conversation_model import Conversation
from fastapi import WebSocket


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    AUTH0_AUDIENCE: str = config('AUTH0_AUDIENCE', cast=str)
    AUTH0_DOMAIN: str = config('AUTH0_DOMAIN', cast=str)
    AUTH0_CLIENT_ID: str = config('AUTH0_CLIENT_ID', cast=str)
    AUTH0_CLIENT_SECRET: str = config('AUTH0_CLIENT_SECRET', cast=str)
    AUTH0_ALGORITHMS: str = config('AUTH0_ALGORITHMS', cast=str)
    AUTH0_ISSUER: str = f"https://{AUTH0_DOMAIN}/"
    OPENAI_API_KEY: str = config('OPENAI_API_KEY', cast=str)
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    PROJECT_NAME: str = "AskTheShelf"
    MONGODB_CONNECTION_STRING: str = config('MONGODB_CONNECTION_STRING', cast=str)
    BASE_URL: str = config('BASE_URL', cast=str)
    GEMINI_API_KEY: str = config('GEMINI_API_KEY', cast=str)
    SCRAPER_URL: str = config('SCRAPER_URL', cast=str)
    GROQ_API_KEY: str = config('GROQ_API_KEY', cast=str)

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


# Handles sockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(message)

    async def send_personal_json(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

    async def broadcast_json(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()
