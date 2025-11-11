"""
Tool operations for conversations.
"""

from datetime import datetime
from typing import Optional

from ...api.models.conversation import EnabledTool
from .storage import ConversationStorage


class ToolOperations:
    """Handles enabled tool operations within conversations."""

    def __init__(self, storage: ConversationStorage):
        """Initialize tool operations."""
        self.storage = storage

    def get_enabled(self, conversation_id: str) -> Optional[list[EnabledTool]]:
        """Get all enabled tools for a conversation."""
        conversation = self.storage.load(conversation_id)
        if not conversation:
            return None
        return conversation.enabled_tools

    def enable(
        self, conversation_id: str, server_id: str, tool_name: str
    ) -> Optional[list[EnabledTool]]:
        """Enable a tool for a conversation."""
        conversation = self.storage.load(conversation_id)
        if not conversation:
            return None

        # Check if already enabled
        for tool in conversation.enabled_tools:
            if tool.server_id == server_id and tool.tool_name == tool_name:
                return conversation.enabled_tools  # Already enabled

        # Add the tool
        enabled_tool = EnabledTool(server_id=server_id, tool_name=tool_name)
        conversation.enabled_tools.append(enabled_tool)
        conversation.updated_at = datetime.utcnow().isoformat() + "Z"
        self.storage.save(conversation)
        return conversation.enabled_tools

    def disable(
        self, conversation_id: str, server_id: str, tool_name: str
    ) -> Optional[list[EnabledTool]]:
        """Disable a tool for a conversation."""
        conversation = self.storage.load(conversation_id)
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
        self.storage.save(conversation)
        return conversation.enabled_tools
