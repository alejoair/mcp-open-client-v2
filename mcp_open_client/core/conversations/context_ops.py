"""
Context operations for conversations.
"""

import uuid
from datetime import datetime
from typing import Optional

from ...api.models.conversation import ContextItem
from .storage import ConversationStorage


class ContextOperations:
    """Handles context operations within conversations."""

    def __init__(self, storage: ConversationStorage):
        """Initialize context operations."""
        self.storage = storage

    def add(
        self,
        conversation_id: str,
        descriptive_name: str,
        content: str,
        related_keywords: Optional[list[str]] = None,
        related_files: Optional[list[str]] = None,
    ) -> Optional[tuple[str, ContextItem]]:
        """Add a context item to a conversation."""
        conversation = self.storage.load(conversation_id)
        if not conversation:
            return None

        context_id = f"ctx-{uuid.uuid4().hex[:16]}"
        context_item = ContextItem(
            descriptive_name=descriptive_name,
            content=content,
            related_keywords=related_keywords or [],
            related_files=related_files or [],
        )

        conversation.context[context_id] = context_item
        conversation.updated_at = datetime.utcnow().isoformat() + "Z"
        self.storage.save(conversation)
        return context_id, context_item

    def get_all(self, conversation_id: str) -> Optional[dict[str, ContextItem]]:
        """Get all context items from a conversation."""
        conversation = self.storage.load(conversation_id)
        if not conversation:
            return None
        return conversation.context

    def update(
        self,
        conversation_id: str,
        context_id: str,
        descriptive_name: Optional[str] = None,
        content: Optional[str] = None,
        related_keywords: Optional[list[str]] = None,
        related_files: Optional[list[str]] = None,
    ) -> Optional[ContextItem]:
        """Update a context item."""
        conversation = self.storage.load(conversation_id)
        if not conversation or context_id not in conversation.context:
            return None

        context_item = conversation.context[context_id]

        if descriptive_name is not None:
            context_item.descriptive_name = descriptive_name
        if content is not None:
            context_item.content = content
        if related_keywords is not None:
            context_item.related_keywords = related_keywords
        if related_files is not None:
            context_item.related_files = related_files

        conversation.updated_at = datetime.utcnow().isoformat() + "Z"
        self.storage.save(conversation)
        return context_item

    def delete(
        self, conversation_id: str, context_id: str
    ) -> Optional[dict[str, ContextItem]]:
        """Delete a context item from a conversation."""
        conversation = self.storage.load(conversation_id)
        if not conversation:
            return None

        if context_id in conversation.context:
            del conversation.context[context_id]
            conversation.updated_at = datetime.utcnow().isoformat() + "Z"
            self.storage.save(conversation)

        return conversation.context
