"""
Conversation storage operations - handles file I/O.
"""

import json
from pathlib import Path
from typing import Optional

from ...api.models.conversation import Conversation
from ...config import get_config_path


class ConversationStorage:
    """Handles persistence of conversations to disk."""

    def __init__(self):
        """Initialize the storage handler."""
        config_dir = get_config_path("")
        self.conversations_dir = config_dir / "conversations"
        self.conversations_dir.mkdir(exist_ok=True)

    def _get_conversation_path(self, conversation_id: str) -> Path:
        """Get the file path for a conversation."""
        return self.conversations_dir / f"{conversation_id}.json"

    def load(self, conversation_id: str) -> Optional[Conversation]:
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

    def save(self, conversation: Conversation) -> None:
        """Save a conversation to disk."""
        path = self._get_conversation_path(conversation.id)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(conversation.model_dump(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Failed to save conversation {conversation.id}: {e}")

    def delete(self, conversation_id: str) -> bool:
        """Delete a conversation from disk."""
        path = self._get_conversation_path(conversation_id)
        if not path.exists():
            return False

        try:
            path.unlink()
            return True
        except Exception as e:
            raise Exception(f"Failed to delete conversation {conversation_id}: {e}")

    def list_all(self) -> list[Conversation]:
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
