"""
Shared dependencies for conversation endpoints.
"""

from ....core.chat_service import ChatService
from ....core.conversations import get_conversation_manager
from ....core.providers import AIProviderManager
from ..servers import get_server_manager

# Get manager instances (shared across all endpoint modules)
conversation_manager = get_conversation_manager()
server_manager = get_server_manager()
chat_service = ChatService()
provider_manager = AIProviderManager()
