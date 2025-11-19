"""
Context endpoints for conversations.
"""

from fastapi import HTTPException, status

from ...models.conversation import (
    ContextCreateRequest,
    ContextResponse,
    ContextUpdateRequest,
)
from ..sse import get_local_sse_service
from . import router
from .dependencies import conversation_manager


@router.post(
    "/{conversation_id}/context",
    response_model=ContextResponse,
    operation_id="conversation_add_context",
)
async def add_context(conversation_id: str, request: ContextCreateRequest):
    """
    Add a context item to a conversation.

    - **conversation_id**: Conversation identifier
    - **descriptive_name**: Descriptive name for the context
    - **related_keywords**: Related keywords
    - **related_files**: Related file paths
    - **content**: Context content
    """
    result = conversation_manager.add_context(
        conversation_id=conversation_id,
        descriptive_name=request.descriptive_name,
        content=request.content,
        related_keywords=request.related_keywords,
        related_files=request.related_files,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    context_id, context_item = result

    # Emit SSE event for context added
    sse_service = get_local_sse_service()
    await sse_service.emit_context_added(
        conversation_id,
        {
            "context_id": context_id,
            "descriptive_name": context_item.descriptive_name,
            "content": context_item.content,
        },
    )

    return ContextResponse(
        success=True,
        context_id=context_id,
        context=context_item,
        message="Context added successfully",
    )


@router.get("/{conversation_id}/context", operation_id="conversation_get_context")
async def get_context(conversation_id: str):
    """
    Get all context items from a conversation.

    - **conversation_id**: Conversation identifier
    """
    context = conversation_manager.get_context(conversation_id)
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return {"success": True, "context": context, "count": len(context)}


@router.put(
    "/{conversation_id}/context/{context_id}",
    response_model=ContextResponse,
    operation_id="conversation_update_context",
)
async def update_context(
    conversation_id: str, context_id: str, request: ContextUpdateRequest
):
    """
    Update a context item.

    - **conversation_id**: Conversation identifier
    - **context_id**: Context item identifier
    """
    context_item = conversation_manager.update_context(
        conversation_id=conversation_id,
        context_id=context_id,
        descriptive_name=request.descriptive_name,
        content=request.content,
        related_keywords=request.related_keywords,
        related_files=request.related_files,
    )

    if not context_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context '{context_id}' not found in conversation '{conversation_id}'",
        )

    # Emit SSE event for context updated
    sse_service = get_local_sse_service()
    await sse_service.emit_context_updated(
        conversation_id,
        {
            "context_id": context_id,
            "descriptive_name": context_item.descriptive_name,
            "content": context_item.content,
        },
    )

    return ContextResponse(
        success=True,
        context_id=context_id,
        context=context_item,
        message="Context updated successfully",
    )


@router.delete(
    "/{conversation_id}/context/{context_id}",
    operation_id="conversation_delete_context",
)
async def delete_context(conversation_id: str, context_id: str):
    """
    Delete a context item from a conversation.

    - **conversation_id**: Conversation identifier
    - **context_id**: Context item identifier
    """
    success = conversation_manager.delete_context(conversation_id, context_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context '{context_id}' not found in conversation '{conversation_id}'",
        )

    # Emit SSE event for context deleted
    sse_service = get_local_sse_service()
    await sse_service.emit_context_deleted(conversation_id, {"context_id": context_id})

    return {"success": True, "message": f"Context '{context_id}' deleted"}


# Tool endpoints
