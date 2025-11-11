"""
Message operations for conversations.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...api.models.conversation import Message
from .storage import ConversationStorage


class MessageOperations:
    """Handles message operations within conversations."""

    def __init__(self, storage: ConversationStorage):
        """Initialize message operations."""
        self.storage = storage

    def add(
        self,
        conversation_id: str,
        role: str,
        content: Optional[str] = None,
        message_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[Message]:
        """Add a message to a conversation."""
        conversation = self.storage.load(conversation_id)
        if not conversation:
            return None

        if not message_id:
            message_id = f"msg-{uuid.uuid4().hex[:16]}"
        if not timestamp:
            timestamp = datetime.utcnow().isoformat() + "Z"

        message = Message(
            id=message_id,
            role=role,
            content=content,
            timestamp=timestamp,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            name=name,
        )

        conversation.messages.append(message)
        conversation.updated_at = datetime.utcnow().isoformat() + "Z"
        self.storage.save(conversation)
        return message

    def get_all(self, conversation_id: str) -> Optional[list[Message]]:
        """Get all messages from a conversation."""
        conversation = self.storage.load(conversation_id)
        if not conversation:
            return None
        return conversation.messages

    def delete(self, conversation_id: str, message_id: str) -> Optional[list[Message]]:
        """Delete a message from a conversation."""
        conversation = self.storage.load(conversation_id)
        if not conversation:
            return None

        original_count = len(conversation.messages)
        conversation.messages = [m for m in conversation.messages if m.id != message_id]

        if len(conversation.messages) == original_count:
            return conversation.messages  # Message not found

        conversation.updated_at = datetime.utcnow().isoformat() + "Z"
        self.storage.save(conversation)
        return conversation.messages
