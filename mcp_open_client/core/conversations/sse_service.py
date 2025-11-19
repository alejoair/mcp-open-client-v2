"""
SSE Service for real-time tool call streaming.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Optional


class SSEService:
    """
    Service for handling Server-Sent Events for tool call streaming.
    """

    def __init__(self):
        self.active_connections: Dict[str, asyncio.Queue] = {}

    async def add_connection(self, conversation_id: str):
        """Add a new SSE connection for a conversation."""
        queue = asyncio.Queue()
        self.active_connections[conversation_id] = queue
        return queue

    async def remove_connection(self, conversation_id: str):
        """Remove an SSE connection for a conversation."""
        if conversation_id in self.active_connections:
            del self.active_connections[conversation_id]

    async def emit_tool_event(
        self, conversation_id: str, event_type: str, data: Dict[str, Any]
    ):
        """
        Emit a tool event to all SSE connections for a conversation.

        Args:
            conversation_id: ID of the conversation
            event_type: Type of event ('tool_call', 'tool_response', 'tool_error')
            data: Event data to send
        """
        if conversation_id in self.active_connections:
            event = {
                "type": event_type,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "data": data,
            }
            await self.active_connections[conversation_id].put(event)

    async def emit_tool_call(
        self, conversation_id: str, tool_call_data: Dict[str, Any]
    ):
        """Emit a tool call event."""
        await self.emit_tool_event(conversation_id, "tool_call", tool_call_data)

    async def emit_tool_response(
        self, conversation_id: str, tool_response_data: Dict[str, Any]
    ):
        """Emit a tool response event."""
        await self.emit_tool_event(conversation_id, "tool_response", tool_response_data)

    async def emit_tool_error(
        self, conversation_id: str, tool_error_data: Dict[str, Any]
    ):
        """Emit a tool error event."""
        await self.emit_tool_event(conversation_id, "tool_error", tool_error_data)

    async def emit_context_added(
        self, conversation_id: str, context_data: Dict[str, Any]
    ):
        """Emit a context added event."""
        await self.emit_tool_event(conversation_id, "context_added", context_data)

    async def emit_context_updated(
        self, conversation_id: str, context_data: Dict[str, Any]
    ):
        """Emit a context updated event."""
        await self.emit_tool_event(conversation_id, "context_updated", context_data)

    async def emit_context_deleted(
        self, conversation_id: str, context_data: Dict[str, Any]
    ):
        """Emit a context deleted event."""
        await self.emit_tool_event(conversation_id, "context_deleted", context_data)


# Global SSE service instance
_sse_service: Optional[SSEService] = None


def get_sse_service() -> SSEService:
    """Get or create the global SSE service instance."""
    global _sse_service
    if _sse_service is None:
        _sse_service = SSEService()
    return _sse_service
