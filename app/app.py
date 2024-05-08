from fastapi import FastAPI, Depends, HTTPException, status, Security, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from app.api.deps.user_deps import get_current_user
from app.core.config import settings, manager
from app.core.security import auth
from app.models.conversation_model import Message, Conversation
from app.api.api_v1.router import router
from app.core.logger import logger
from app.core.middlewares import AuthMiddleware
from app.core.config import init_db
from app.services.conversation_service import ConversationService
from app.services.job_service import JobService
from app.services.llm_service import LLMService, GPT3

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
    "https://www.asktheshelf.com",
    "http://localhost",
    "https://localhost",
    "capacitor://localhost",
    "https://scraper-dev.up.railway.app",
    "https://asktheshelf-fontend-dev.up.railway.app"
]


# TODO: Refactor this to not have if else statements
async def chat_with_llm(query, user_id, model):
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
        user_conversation.messages.append(user_message)
        await ConversationService.update_conversation(user_id, user_conversation)
        assistant_message = await LLMService.get_action_from_llm(query, user_conversation, model)
        user_conversation.messages.append(assistant_message)
        await ConversationService.update_conversation(user_id, user_conversation)
        return assistant_message

    except Exception as e:
        assistant_message = Message(
            role="assistant",
            content="I'm sorry, I encountered an error while processing your request"
        )
        user_conversation = await ConversationService.get_conversation_by_user_id(user_id)
        user_conversation.messages.append(assistant_message)
        await ConversationService.update_conversation(user_id, user_conversation)
        logger.error(e)
        return assistant_message


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
                logger.info(f"User {user_id} connected")
                continue
            elif data.get("type") == "message":
                message = data.get("message")
                model = data.get("model")
                response = await chat_with_llm(message, user_id, model)
                await manager.send_personal_json(response.json(), user_id)
            elif data.get("type") == "link":
                url = data.get("url")
                response = await JobService.get_comprehensive_product_details(user_id, url)
                await manager.send_personal_json(response.json(), user_id)
            else:
                assistant_message = Message(
                    role="assistant",
                    content="Invalid message type",
                )
                await manager.send_personal_json(assistant_message.json(), user_id)
    except WebSocketDisconnect:
        manager.disconnect(user_id)  # Clean up on disconnect
        print(f"User {user_id} disconnected")
    except Exception as e:
        print(f"Error with WebSocket for user {user_id}: {e}")
        # await websocket.close(code=1011)  # Internal server error code


@app.on_event("startup")
async def app_startup():
    try:
        await init_db()
    except Exception as e:
        logger.error(f"An error occurred while connecting to database: {e}")


# Not sure if this is working
@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred"},
    )


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
