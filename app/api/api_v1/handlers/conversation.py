from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer
from app.models.conversation_model import Conversation

from app.services.conversation_service import ConversationService

conversation_router = APIRouter(dependencies=[Depends(HTTPBearer())])


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
