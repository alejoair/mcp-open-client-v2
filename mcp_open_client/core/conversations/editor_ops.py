"""
Open editor operations for conversations.
"""

from datetime import datetime
from typing import Optional

from ...api.models.conversation import OpenEditor
from .storage import ConversationStorage


class EditorOperations:
    """Handles open editor operations within conversations."""

    def __init__(self, storage: ConversationStorage):
        """Initialize editor operations."""
        self.storage = storage

    def get_all(self, conversation_id: str) -> Optional[list[OpenEditor]]:
        """Get all open editors for a conversation."""
        conversation = self.storage.load(conversation_id)
        if not conversation:
            return None
        return conversation.open_editors

    def add(
        self,
        conversation_id: str,
        file_path: str,
        language: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> Optional[list[OpenEditor]]:
        """Add an open editor to a conversation."""
        conversation = self.storage.load(conversation_id)
        if not conversation:
            return None

        # Check if editor already exists
        for editor in conversation.open_editors:
            if editor.file_path == file_path:
                # Update existing editor
                if language is not None:
                    editor.language = language
                if line_number is not None:
                    editor.line_number = line_number
                conversation.updated_at = datetime.utcnow().isoformat() + "Z"
                self.storage.save(conversation)
                return conversation.open_editors

        # Add new editor
        editor = OpenEditor(
            file_path=file_path, language=language, line_number=line_number
        )
        conversation.open_editors.append(editor)
        conversation.updated_at = datetime.utcnow().isoformat() + "Z"
        self.storage.save(conversation)
        return conversation.open_editors

    def remove(
        self, conversation_id: str, file_path: str
    ) -> Optional[list[OpenEditor]]:
        """Remove an open editor from a conversation."""
        conversation = self.storage.load(conversation_id)
        if not conversation:
            return None

        original_count = len(conversation.open_editors)
        conversation.open_editors = [
            e for e in conversation.open_editors if e.file_path != file_path
        ]

        if len(conversation.open_editors) == original_count:
            return conversation.open_editors  # Editor not found

        conversation.updated_at = datetime.utcnow().isoformat() + "Z"
        self.storage.save(conversation)
        return conversation.open_editors
