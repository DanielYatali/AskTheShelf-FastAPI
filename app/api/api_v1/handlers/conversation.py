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
