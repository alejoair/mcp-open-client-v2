"""
Conversation Manager - Facade that coordinates all conversation operations.
"""

from typing import Optional

from ...api.models.conversation import (
    ContextItem,
    Conversation,
    EnabledTool,
    Message,
    OpenEditor,
)
from .chat_ops import ChatOperations
from .context_ops import ContextOperations
from .conversation_ops import ConversationOperations
from .editor_ops import EditorOperations
from .message_ops import MessageOperations
from .storage import ConversationStorage
from .tool_ops import ToolOperations


class ConversationManager:
    """
    Main facade for conversation management.

    Coordinates all conversation-related operations by delegating to specialized handlers.
    """

    def __init__(self):
        """Initialize the conversation manager."""
        # Initialize storage
        self.storage = ConversationStorage()

        # Initialize operation handlers
        self.conversations = ConversationOperations(self.storage)
        self.messages = MessageOperations(self.storage)
        self.context = ContextOperations(self.storage)
        self.tools = ToolOperations(self.storage)
        self.editors = EditorOperations(self.storage)
        self.chat = ChatOperations(self.storage)

    # Conversation operations

    def create_conversation(
        self,
        title: str,
        description: str = "",
        system_prompt: str = "You are a helpful AI assistant.",
        max_tokens: Optional[int] = 20000,
        max_messages: Optional[int] = 100,
    ) -> Conversation:
        """Create a new conversation."""
        return self.conversations.create(
            title, description, system_prompt, max_tokens, max_messages
        )

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        return self.conversations.get(conversation_id)

    def update_conversation(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        max_messages: Optional[int] = None,
    ) -> Optional[Conversation]:
        """Update conversation metadata."""
        return self.conversations.update(
            conversation_id, title, description, system_prompt, max_tokens, max_messages
        )

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        return self.conversations.delete(conversation_id)

    def list_conversations(self) -> list[Conversation]:
        """List all conversations."""
        return self.conversations.list_all()

    def search_conversations(self, query: str) -> list[Conversation]:
        """Search conversations by title, description, or keywords."""
        return self.conversations.search(query)

    # Message operations

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: Optional[str] = None,
        message_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        tool_calls: Optional[list] = None,
        tool_call_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[Message]:
        """Add a message to a conversation."""
        return self.messages.add(
            conversation_id,
            role,
            content,
            message_id,
            timestamp,
            tool_calls,
            tool_call_id,
            name,
        )

    def get_messages(self, conversation_id: str) -> Optional[list[Message]]:
        """Get all messages from a conversation."""
        return self.messages.get_all(conversation_id)

    def delete_message(
        self, conversation_id: str, message_id: str
    ) -> Optional[list[Message]]:
        """Delete a message from a conversation."""
        return self.messages.delete(conversation_id, message_id)

    # Context operations

    def add_context(
        self,
        conversation_id: str,
        descriptive_name: str,
        content: str,
        related_keywords: Optional[list[str]] = None,
        related_files: Optional[list[str]] = None,
    ) -> Optional[tuple[str, ContextItem]]:
        """Add a context item to a conversation."""
        return self.context.add(
            conversation_id,
            descriptive_name,
            content,
            related_keywords,
            related_files,
        )

    def get_context(self, conversation_id: str) -> Optional[dict[str, ContextItem]]:
        """Get all context items from a conversation."""
        return self.context.get_all(conversation_id)

    def update_context(
        self,
        conversation_id: str,
        context_id: str,
        descriptive_name: Optional[str] = None,
        content: Optional[str] = None,
        related_keywords: Optional[list[str]] = None,
        related_files: Optional[list[str]] = None,
    ) -> Optional[ContextItem]:
        """Update a context item."""
        return self.context.update(
            conversation_id,
            context_id,
            descriptive_name,
            content,
            related_keywords,
            related_files,
        )

    def delete_context(
        self, conversation_id: str, context_id: str
    ) -> Optional[dict[str, ContextItem]]:
        """Delete a context item from a conversation."""
        return self.context.delete(conversation_id, context_id)

    # Tool operations

    def get_tools(self, conversation_id: str) -> Optional[list[EnabledTool]]:
        """Get all enabled tools for a conversation."""
        return self.tools.get_enabled(conversation_id)

    def enable_tool(
        self, conversation_id: str, server_id: str, tool_name: str
    ) -> Optional[list[EnabledTool]]:
        """Enable a tool for a conversation."""
        return self.tools.enable(conversation_id, server_id, tool_name)

    def disable_tool(
        self, conversation_id: str, server_id: str, tool_name: str
    ) -> Optional[list[EnabledTool]]:
        """Disable a tool for a conversation."""
        return self.tools.disable(conversation_id, server_id, tool_name)

    # Editor operations

    def get_open_editors(self, conversation_id: str) -> Optional[list[OpenEditor]]:
        """Get all open editors for a conversation."""
        return self.editors.get_all(conversation_id)

    def add_open_editor(
        self,
        conversation_id: str,
        file_path: str,
        language: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> Optional[list[OpenEditor]]:
        """Add an open editor to a conversation."""
        return self.editors.add(conversation_id, file_path, language, line_number)

    def remove_open_editor(
        self, conversation_id: str, file_path: str
    ) -> Optional[list[OpenEditor]]:
        """Remove an open editor from a conversation."""
        return self.editors.remove(conversation_id, file_path)

    # Chat operations

    def prepare_chat_messages(
        self, conversation_id: str, new_user_message: str
    ) -> Optional[tuple[str, list[dict[str, str]], list, int, int]]:
        """Prepare messages for LLM based on conversation data."""
        return self.chat.prepare_messages(conversation_id, new_user_message)


# Global conversation manager instance
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """Get or create the global conversation manager instance."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
