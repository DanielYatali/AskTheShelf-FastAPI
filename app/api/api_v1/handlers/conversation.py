import asyncio
import json
from typing import Dict

from beanie import PydanticObjectId
from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer
from fastapi.responses import StreamingResponse

from app.core.logger import logger
from app.models.conversation_model import Conversation

from app.services.conversation_service import ConversationService

conversation_router = APIRouter()


@conversation_router.get("/stream")
async def get_user_conversations_stream(request: Request):
    # This code runs once per connection
    user = request.state.user
    user_id = user.user_id
    conversation = await ConversationService.get_conversation_by_user_id(user_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    conversation_id = conversation.id
    logger.info(f"Starting stream for conversation {conversation_id}")

    return StreamingResponse(event_generator(request,user_id, conversation_id), media_type="text/event-stream")

async def event_generator(request, user_id, conversation_id):
    # This code runs in a loop, once every 5 seconds
    while True:
        if request.is_disconnected():
            break
        logger.info(f"Waiting for changes for document {conversation_id}")
        conversation = await ConversationService.get_conversation_by_user_id(user_id)
        if not conversation:
            yield "data: {}\n\n"  # Send empty data if no conversation found
        else:
            # Serialize the conversation data to JSON string
            conversation_data = conversation.json()
            yield f"data: {conversation_data}\n\n"
        await asyncio.sleep(5)  # Wait for 5 seconds before sending the next update

# async def get_user_conversations_stream(request: Request):
#     user = request.state.user
#     user_id = user.user_id
#     collection = Conversation.get_motor_collection()
#     conversation = await ConversationService.get_conversation_by_user_id(user_id)
#     if not conversation:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
#     # find the conversation id
#
#     conversation_id = conversation.id
#
#     logger.info(f"Starting change stream for user {user_id}")
#
#     # Setup the change stream
#     # thins is not working
#
#     # pipeline = [{"$match": {"fullDocument._id": PydanticObjectId(conversation_id)}}]
#     # change_stream = collection.watch(pipeline)
#
#     async def event_generator():
#         try:
#             while True:
#                 logger.info(f"Waiting for changes for document {conversation_id}")
#                 # change = await change_stream.try_next()
#                 change = await collection.find_one({"_id": PydanticObjectId(conversation_id)})
#                 if change is None:
#                     await asyncio.sleep(5)  # No change available, sleep to prevent busy loop
#                     continue
#                 if request.is_disconnected():
#                     break
#                 yield f"data: {change['fullDocument']}\n\n"
#         except asyncio.CancelledError:
#             pass
#         finally:
#             await collection.close()
#
#     return StreamingResponse(event_generator(), media_type="text/event-stream")


@conversation_router.get("/{user_id}", summary="Get conversations by user",
                         response_model=Conversation or HTTPException)
async def get_conversations(request: Request) -> Conversation:
    user = request.state.user
    conversations = await ConversationService.get_conversation_by_user_id(user.user_id)
    if not conversations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversations


@conversation_router.delete("/{conversation_id}", summary="Delete conversation by id")
async def delete_conversation(request: Request) -> dict[str, str]:
    user = request.state.user
    conversation = await ConversationService.delete_conversation(user.user_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return {"message": "Conversation deleted successfully"}
