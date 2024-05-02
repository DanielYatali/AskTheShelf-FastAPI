from datetime import datetime
from typing import Optional

from app.core.logger import logger
from app.models.conversation_model import Conversation


class ConversationService:
    @staticmethod
    async def create_conversation(conversation: Conversation) -> Optional[Conversation]:
        await conversation.save()
        return conversation

    @staticmethod
    async def get_conversation_by_user_id(user_id: str) -> Optional[Conversation]:
        conversation = await Conversation.find_one(Conversation.user_id == user_id)
        if not conversation:
            return None
        return conversation

    @staticmethod
    async def get_conversations():
        conversations = await Conversation.all().to_list()
        return conversations

    @staticmethod
    async def update_conversation(user_id: str, conversation: Conversation) -> Optional[Conversation]:
        existing_conversation = await Conversation.find_one(Conversation.user_id == user_id)
        if not existing_conversation:
            logger.warning(f"No conversation found for user_id: {user_id}")
            return None
        if len(conversation.messages) > 50:
            conversation.messages.pop(0)
        existing_conversation.messages = conversation.messages
        existing_conversation.updated_at = datetime.now()
        await existing_conversation.save()
        return existing_conversation

    @staticmethod
    async def delete_conversation(user_id: str) -> Optional[Conversation]:
        conversation = await Conversation.find_one(Conversation.user_id == user_id)
        if not conversation:
            return None
        await conversation.delete()
        return conversation
