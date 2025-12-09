"""
Message endpoints for conversations.
"""

from fastapi import HTTPException, status

from ...models.conversation import MessageCreateRequest, MessageResponse
from . import router
from .dependencies import conversation_manager


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    operation_id="conversation_add_message",
)
async def add_message(conversation_id: str, request: MessageCreateRequest):
    """
    Add a message to a conversation.

    - **conversation_id**: Conversation identifier
    - **role**: Message role (user, assistant, system)
    - **content**: Message content
    """
    message = conversation_manager.add_message(
        conversation_id=conversation_id, role=request.role, content=request.content
    )

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return MessageResponse(
        success=True, message=message, result_message="Message added successfully"
    )


@router.get("/{conversation_id}/messages", operation_id="conversation_get_messages")
async def get_messages(conversation_id: str):
    """
    Get all messages from a conversation.

    - **conversation_id**: Conversation identifier
    """
    messages = conversation_manager.get_messages(conversation_id)
    if messages is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return {"success": True, "messages": messages, "count": len(messages)}


@router.delete(
    "/{conversation_id}/messages/{message_id}",
    operation_id="conversation_delete_message",
)
async def delete_message(conversation_id: str, message_id: str):
    """
    Delete a specific message from a conversation.

    - **conversation_id**: Conversation identifier
    - **message_id**: Message identifier
    """
    success = conversation_manager.delete_message(conversation_id, message_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message '{message_id}' not found in conversation '{conversation_id}'",
        )

    return {"success": True, "message": f"Message '{message_id}' deleted"}
