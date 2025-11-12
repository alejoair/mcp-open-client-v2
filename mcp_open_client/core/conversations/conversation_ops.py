"""
Conversation CRUD operations.
"""

import uuid
from datetime import datetime
from typing import Optional

from ...api.models.conversation import Conversation
from .storage import ConversationStorage


class ConversationOperations:
    """Handles conversation CRUD operations."""

    def __init__(self, storage: ConversationStorage):
        """Initialize conversation operations."""
        self.storage = storage

    def create(
        self,
        title: str,
        description: str = "",
        system_prompt: str = "You are a helpful AI assistant.",
        max_tokens: Optional[int] = 20000,
        max_messages: Optional[int] = 100,
    ) -> Conversation:
        """Create a new conversation."""
        conversation_id = f"conv-{uuid.uuid4().hex[:16]}"
        now = datetime.utcnow().isoformat() + "Z"

        conversation = Conversation(
            id=conversation_id,
            title=title,
            description=description,
            created_at=now,
            updated_at=now,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            max_messages=max_messages,
            enabled_tools=[],
            open_editors=[],
            context={},
            messages=[],
        )

        self.storage.save(conversation)
        return conversation

    def get(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        return self.storage.load(conversation_id)

    def update(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        max_messages: Optional[int] = None,
    ) -> Optional[Conversation]:
        """Update conversation metadata."""
        conversation = self.storage.load(conversation_id)
        if not conversation:
            return None

        if title is not None:
            conversation.title = title
        if description is not None:
            conversation.description = description
        if system_prompt is not None:
            conversation.system_prompt = system_prompt
        if max_tokens is not None:
            conversation.max_tokens = max_tokens
        if max_messages is not None:
            conversation.max_messages = max_messages

        conversation.updated_at = datetime.utcnow().isoformat() + "Z"
        self.storage.save(conversation)
        return conversation

    def delete(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        return self.storage.delete(conversation_id)

    def list_all(self) -> list[Conversation]:
        """List all conversations."""
        return self.storage.list_all()

    def search(self, query: str) -> list[Conversation]:
        """Search conversations by title, description, or keywords."""
        query_lower = query.lower()
        conversations = self.list_all()
        results = []

        for conversation in conversations:
            # Search in title and description
            if (
                query_lower in conversation.title.lower()
                or query_lower in conversation.description.lower()
            ):
                results.append(conversation)
                continue

            # Search in context keywords
            for context_item in conversation.context.values():
                if any(
                    query_lower in kw.lower() for kw in context_item.related_keywords
                ):
                    results.append(conversation)
                    break

        return results
