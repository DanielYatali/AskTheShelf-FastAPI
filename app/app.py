import asyncio

from fastapi import FastAPI, Depends, HTTPException, status, Security, Request
from fastapi.responses import JSONResponse
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
from sse_starlette.sse import EventSourceResponse

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=None,
)
allowed_origins = [
    "http://localhost:3000",  # Assuming your frontend runs on localhost:3000
    "https://asktheshelf.up.railway.app",
    "http://localhost:6800",
    "https://asktheshelfscraper.up.railway.app",
    "https://www.asktheshelf.com"
]


@app.on_event("startup")
async def app_startup():
    try:
        await init_db()
    except Exception as e:
        logger.error(f"An error occurred while connecting to database: {e}")


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred"},
    )


# async def event_generator(request: Request, user_id: str):
#     pubsub = redis.pubsub()
#     # Subscribe to the user-specific updates channel
#     await pubsub.subscribe(f'user_updates:{user_id}')
#     try:
#         while True:
#             if await request.is_disconnected():
#                 break
#             message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
#             if message and message['type'] == 'message':
#                 job_id = message['data'].decode()
#                 job_status = await redis.hget(f"job:{job_id}", "status")
#                 if job_status == "completed":
#                     job_details = await redis.hget(f"job:{job_id}", "details")
#                     yield f"data: {job_details}\n\n"
#             else:
#                 await asyncio.sleep(1)  # Sleep if no message to reduce CPU usage
#     finally:
#         await pubsub.unsubscribe(f'user_updates:{user_id}')
#         await pubsub.close()
#
#
# @app.get("/events/{user_id}")
# async def events(request: Request, user_id: str):
#     event_generator_instance = event_generator(request, user_id)
#     return EventSourceResponse(event_generator_instance)
#
#
# @app.get("/test")
# async def test_redis():
#     await redis.set('my-key', 'value')
#     value = await redis.get('my-key')
#     return {"value": value}


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
                                                 "/api/v1/scrapy/update", "/test"])
