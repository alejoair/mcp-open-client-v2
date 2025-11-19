"""
Server-Sent Events endpoints for real-time tool call streaming.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse


# Local SSE service to avoid circular imports
class LocalSSEService:
    def __init__(self):
        self.active_connections: Dict[str, asyncio.Queue] = {}

    async def add_connection(self, conversation_id: str):
        queue = asyncio.Queue()
        self.active_connections[conversation_id] = queue
        return queue

    async def remove_connection(self, conversation_id: str):
        if conversation_id in self.active_connections:
            del self.active_connections[conversation_id]

    async def emit_tool_event(
        self, conversation_id: str, event_type: str, data: Dict[str, Any]
    ):
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
        await self.emit_tool_event(conversation_id, "tool_call", tool_call_data)

    async def emit_tool_response(
        self, conversation_id: str, tool_response_data: Dict[str, Any]
    ):
        await self.emit_tool_event(conversation_id, "tool_response", tool_response_data)

    async def emit_tool_error(
        self, conversation_id: str, tool_error_data: Dict[str, Any]
    ):
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
_local_sse_service: Optional[LocalSSEService] = None


def get_local_sse_service():
    global _local_sse_service
    if _local_sse_service is None:
        _local_sse_service = LocalSSEService()
    return _local_sse_service


router = APIRouter(prefix="/sse", tags=["sse"])


@router.get("/conversations/{conversation_id}", operation_id="conversation_sse_stream")
async def sse_conversation_stream(conversation_id: str, request: Request):
    """
    Server-Sent Events endpoint for real-time conversation updates.
    Streams tool calls and responses as they happen.
    """
    sse_service = get_local_sse_service()
    queue = await sse_service.add_connection(conversation_id)

    async def event_generator():
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'conversation_id': conversation_id, 'timestamp': datetime.now().isoformat()})}\n\n"

            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                # Wait for events with timeout
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive every 30 seconds
                    yield f"data: {json.dumps({'type': 'keepalive', 'timestamp': datetime.now().isoformat()})}\n\n"

        except asyncio.CancelledError:
            pass
        finally:
            # Clean up connection
            await sse_service.remove_connection(conversation_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


async def emit_tool_event(conversation_id: str, event_type: str, data: Dict[str, Any]):
    """
    Emit a tool event to all SSE connections for a conversation.

    Args:
        conversation_id: ID of the conversation
        event_type: Type of event ('tool_call', 'tool_response', 'tool_error')
        data: Event data to send
    """
    sse_service = get_local_sse_service()
    await sse_service.emit_tool_event(conversation_id, event_type, data)


async def emit_tool_call(conversation_id: str, tool_call_data: Dict[str, Any]):
    """Emit a tool call event."""
    sse_service = get_local_sse_service()
    await sse_service.emit_tool_call(conversation_id, tool_call_data)


async def emit_tool_response(conversation_id: str, tool_response_data: Dict[str, Any]):
    """Emit a tool response event."""
    sse_service = get_local_sse_service()
    await sse_service.emit_tool_response(conversation_id, tool_response_data)


async def emit_tool_error(conversation_id: str, tool_error_data: Dict[str, Any]):
    """Emit a tool error event."""
    sse_service = get_local_sse_service()
    await sse_service.emit_tool_error(conversation_id, tool_error_data)
