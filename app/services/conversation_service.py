from typing import Optional

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
            return None
        existing_conversation.messages = conversation.messages
        existing_conversation.updated_at = conversation.updated_at
        if len(existing_conversation.messages) > 30:
            existing_conversation.messages.pop(0)
        await existing_conversation.save()
        return existing_conversation

    @staticmethod
    async def delete_conversation(user_id: str) -> Optional[Conversation]:
        conversation = await Conversation.find_one(Conversation.user_id == user_id)
        if not conversation:
            return None
        await conversation.delete()
        return conversation
