import asyncio
import json
from typing import Dict

from fastapi import FastAPI, Depends, HTTPException, status, Security, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from app.api.deps.user_deps import get_current_user
from app.core.config import settings, manager
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.security import auth
from app.models.conversation_model import Message, Conversation
from app.models.user_model import User
from app.models.job_model import Job
from app.models.product_model import Product
from app.api.api_v1.router import router
from app.core.logger import logger
from app.core.middlewares import AuthMiddleware
from app.core.config import init_db

from app.services.conversation_service import ConversationService
from app.services.llm_service import LLMService

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





async def chat_with_llm(query, user_id):
    try:
        if not query:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query not provided")
        user_conversation = await ConversationService.get_conversation_by_user_id(user_id)
        if not user_conversation:
            conversation = Conversation(user_id=user_id, messages=[])
            user_conversation = await ConversationService.create_conversation(conversation)
        user_message = Message(
            role="user",
            content=query,
        )
        response = await LLMService.get_action_from_llm(query, user_conversation)
        user_conversation.messages.append(user_message)
        if isinstance(response, dict):
            if 'products' in response:
                assistant_message = Message(
                    role="assistant",
                    content=response['message'],
                    products=response['products'],
                )
                user_conversation.messages.append(assistant_message)
                await ConversationService.update_conversation(user_id, user_conversation)
                return assistant_message
            else:
                assistant_message = Message(
                    role="assistant",
                    content=response['message'],
                    related_products=response['related_products'],
                )
                user_conversation.messages.append(assistant_message)
                await ConversationService.update_conversation(user_id, user_conversation)
                return assistant_message
        else:
            assistant_message = Message(
                role="assistant",
                content=response,
            )
            user_conversation.messages.append(assistant_message)
            await ConversationService.update_conversation(user_id, user_conversation)
            return assistant_message

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="Error chatting with LLM")


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)  # Manage connection
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "auth":
                token = data.get("token")
                auth_result = await auth.verify_token(token)
                user = await get_current_user(auth_result, token)
                if user is None:
                    await websocket.close(code=1008)
                    return
                if user.user_id != user_id:
                    await websocket.close(code=1008)
                    return
                print(f"User {user_id} connected")
                continue
            elif data.get("type") == "message":
                message = data.get("message")
                response = await chat_with_llm(message, user_id)
                await manager.send_personal_json(response.json(), user_id)
            else:
                await websocket.send_json({"error": "Invalid message type"})


            # Process each message received
            # test_message = Message(
            #     role="user",
            #     content="test message",
            # )
            # await manager.send_personal_json(test_message.json(), user_id)
            # Example of broadcasting a received message
            # await manager.broadcast(f"User {user_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(user_id)  # Clean up on disconnect
        print(f"User {user_id} disconnected")
    except Exception as e:
        print(f"Error with WebSocket for user {user_id}: {e}")
        await websocket.close(code=1011)  # Internal server error code


async def process_message(message, websocket):
    # Handle messages here, e.g., parsing and responding back to the same user
    await websocket.send_text(f"Echo: {message}")


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
