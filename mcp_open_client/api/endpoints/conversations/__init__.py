"""
Conversation endpoints package.
"""

from fastapi import APIRouter

# Create shared router
router = APIRouter(prefix="/conversations", tags=["conversations"])

# Import all endpoint modules (they will register themselves with the router)
from . import chat_endpoints  # noqa: F401
from . import context_endpoints  # noqa: F401
from . import conversations_endpoints  # noqa: F401
from . import editors_endpoints  # noqa: F401
from . import messages_endpoints  # noqa: F401
from . import tools_endpoints  # noqa: F401

__all__ = ["router"]
