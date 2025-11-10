"""
Conversation Manager - Manages conversation storage and operations.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..api.models.conversation import (
    ContextItem,
    Conversation,
    EnabledTool,
    Message,
)
from ..config import get_config_path


class ConversationManager:
    """Manages conversation persistence and operations."""

    def __init__(self):
        """Initialize the conversation manager."""
        # Get conversations directory from config
        config_dir = Path(get_config_path("")).parent
        self.conversations_dir = config_dir / "conversations"
        self.conversations_dir.mkdir(exist_ok=True)

    def _get_conversation_path(self, conversation_id: str) -> Path:
        """Get the file path for a conversation."""
        return self.conversations_dir / f"{conversation_id}.json"

    def _load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Load a conversation from disk."""
        path = self._get_conversation_path(conversation_id)
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Conversation(**data)
        except Exception as e:
            raise Exception(f"Failed to load conversation {conversation_id}: {e}")

    def _save_conversation(self, conversation: Conversation) -> None:
        """Save a conversation to disk."""
        path = self._get_conversation_path(conversation.id)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(conversation.model_dump(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Failed to save conversation {conversation.id}: {e}")

    def create_conversation(
        self,
        title: str,
        description: str = "",
        system_prompt: str = "You are a helpful AI assistant.",
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
            enabled_tools=[],
            context={},
            messages=[],
        )

        self._save_conversation(conversation)
        return conversation

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        return self._load_conversation(conversation_id)

    def list_conversations(self) -> List[Conversation]:
        """List all conversations."""
        conversations = []
        for file_path in self.conversations_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    conversations.append(Conversation(**data))
            except Exception:
                # Skip invalid files
                continue

        # Sort by updated_at descending
        conversations.sort(key=lambda c: c.updated_at, reverse=True)
        return conversations

    def update_conversation(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Optional[Conversation]:
        """Update conversation metadata."""
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return None

        if title is not None:
            conversation.title = title
        if description is not None:
            conversation.description = description
        if system_prompt is not None:
            conversation.system_prompt = system_prompt

        conversation.updated_at = datetime.utcnow().isoformat() + "Z"
        self._save_conversation(conversation)
        return conversation

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        path = self._get_conversation_path(conversation_id)
        if not path.exists():
            return False

        try:
            path.unlink()
            return True
        except Exception:
            return False

    # Message operations

    def add_message(
        self, conversation_id: str, role: str, content: str
    ) -> Optional[Message]:
        """Add a message to a conversation."""
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return None

        message_id = f"msg-{uuid.uuid4().hex[:12]}"
        timestamp = datetime.utcnow().isoformat() + "Z"

        message = Message(
            id=message_id, role=role, content=content, timestamp=timestamp
        )
        conversation.messages.append(message)
        conversation.updated_at = timestamp

        self._save_conversation(conversation)
        return message

    def get_messages(self, conversation_id: str) -> Optional[List[Message]]:
        """Get all messages from a conversation."""
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return None
        return conversation.messages

    def delete_message(self, conversation_id: str, message_id: str) -> bool:
        """Delete a specific message from a conversation."""
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return False

        original_count = len(conversation.messages)
        conversation.messages = [m for m in conversation.messages if m.id != message_id]

        if len(conversation.messages) == original_count:
            return False  # Message not found

        conversation.updated_at = datetime.utcnow().isoformat() + "Z"
        self._save_conversation(conversation)
        return True

    # Context operations

    def add_context(
        self,
        conversation_id: str,
        descriptive_name: str,
        content: str,
        related_keywords: Optional[List[str]] = None,
        related_files: Optional[List[str]] = None,
    ) -> Optional[tuple[str, ContextItem]]:
        """Add a context item to a conversation."""
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return None

        context_id = f"ctx-{uuid.uuid4().hex[:12]}"
        context_item = ContextItem(
            descriptive_name=descriptive_name,
            content=content,
            related_keywords=related_keywords or [],
            related_files=related_files or [],
        )

        conversation.context[context_id] = context_item
        conversation.updated_at = datetime.utcnow().isoformat() + "Z"

        self._save_conversation(conversation)
        return (context_id, context_item)

    def get_context(self, conversation_id: str) -> Optional[Dict[str, ContextItem]]:
        """Get all context items from a conversation."""
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return None
        return conversation.context

    def update_context(
        self,
        conversation_id: str,
        context_id: str,
        descriptive_name: Optional[str] = None,
        content: Optional[str] = None,
        related_keywords: Optional[List[str]] = None,
        related_files: Optional[List[str]] = None,
    ) -> Optional[ContextItem]:
        """Update a context item."""
        conversation = self._load_conversation(conversation_id)
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
        self._save_conversation(conversation)
        return context_item

    def delete_context(self, conversation_id: str, context_id: str) -> bool:
        """Delete a context item from a conversation."""
        conversation = self._load_conversation(conversation_id)
        if not conversation or context_id not in conversation.context:
            return False

        del conversation.context[context_id]
        conversation.updated_at = datetime.utcnow().isoformat() + "Z"
        self._save_conversation(conversation)
        return True

    # Tool operations

    def add_enabled_tool(
        self, conversation_id: str, server_id: str, tool_name: str
    ) -> Optional[List[EnabledTool]]:
        """Add an enabled tool to a conversation."""
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return None

        # Check if tool already enabled
        for tool in conversation.enabled_tools:
            if tool.server_id == server_id and tool.tool_name == tool_name:
                return conversation.enabled_tools  # Already enabled

        enabled_tool = EnabledTool(server_id=server_id, tool_name=tool_name)
        conversation.enabled_tools.append(enabled_tool)
        conversation.updated_at = datetime.utcnow().isoformat() + "Z"

        self._save_conversation(conversation)
        return conversation.enabled_tools

    def remove_enabled_tool(
        self, conversation_id: str, server_id: str, tool_name: str
    ) -> Optional[List[EnabledTool]]:
        """Remove an enabled tool from a conversation."""
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return None

        original_count = len(conversation.enabled_tools)
        conversation.enabled_tools = [
            t
            for t in conversation.enabled_tools
            if not (t.server_id == server_id and t.tool_name == tool_name)
        ]

        if len(conversation.enabled_tools) == original_count:
            return conversation.enabled_tools  # Tool not found

        conversation.updated_at = datetime.utcnow().isoformat() + "Z"
        self._save_conversation(conversation)
        return conversation.enabled_tools

    def get_enabled_tools(self, conversation_id: str) -> Optional[List[EnabledTool]]:
        """Get all enabled tools for a conversation."""
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return None
        return conversation.enabled_tools

    # Search operations

    def search_conversations(self, query: str) -> List[Conversation]:
        """Search conversations by title, description, or keywords."""
        query_lower = query.lower()
        conversations = self.list_conversations()
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


# Global conversation manager instance
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """Get or create the global conversation manager instance."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
