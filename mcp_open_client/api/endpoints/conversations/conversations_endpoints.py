"""
Basic CRUD endpoints for conversations.
"""

from fastapi import HTTPException, Query, status

from ...models.conversation import (
    ConversationCreateRequest,
    ConversationListResponse,
    ConversationResponse,
    ConversationSearchResponse,
    ConversationUpdateRequest,
)
from . import router
from .dependencies import conversation_manager


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="conversation_create",
)
async def create_conversation(request: ConversationCreateRequest):
    """
    Create a new conversation.

    - **title**: Conversation title
    - **description**: Optional description
    - **system_prompt**: Optional system prompt
    """
    try:
        conversation = conversation_manager.create_conversation(
            title=request.title,
            description=request.description,
            system_prompt=request.system_prompt,
            max_tokens=request.max_tokens,
            max_messages=request.max_messages,
        )
        return ConversationResponse(
            success=True,
            conversation=conversation,
            message=f"Conversation '{conversation.title}' created successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}",
        )


@router.get(
    "", response_model=ConversationListResponse, operation_id="conversation_list_all"
)
async def list_conversations():
    """
    List all conversations ordered by last update.
    """
    try:
        conversations = conversation_manager.list_conversations()
        return ConversationListResponse(
            success=True, conversations=conversations, count=len(conversations)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list conversations: {str(e)}",
        )


@router.get(
    "/search",
    response_model=ConversationSearchResponse,
    operation_id="conversation_search",
)
async def search_conversations(
    q: str = Query(..., description="Search query for title, description, or keywords")
):
    """
    Search conversations by title, description, or context keywords.

    - **q**: Search query string
    """
    try:
        results = conversation_manager.search_conversations(q)
        return ConversationSearchResponse(
            success=True,
            conversations=results,
            count=len(results),
            message=f"Found {len(results)} conversations matching '{q}'",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    operation_id="conversation_get",
)
async def get_conversation(conversation_id: str):
    """
    Get a specific conversation by ID.

    - **conversation_id**: Conversation identifier
    """
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return ConversationResponse(
        success=True,
        conversation=conversation,
        message=f"Retrieved conversation '{conversation.title}'",
    )


@router.put(
    "/{conversation_id}",
    response_model=ConversationResponse,
    operation_id="conversation_update",
)
async def update_conversation(conversation_id: str, request: ConversationUpdateRequest):
    """
    Update conversation metadata.

    - **conversation_id**: Conversation identifier
    - **title**: New title (optional)
    - **description**: New description (optional)
    - **system_prompt**: New system prompt (optional)
    """
    conversation = conversation_manager.update_conversation(
        conversation_id=conversation_id,
        title=request.title,
        description=request.description,
        system_prompt=request.system_prompt,
        max_tokens=request.max_tokens,
        max_messages=request.max_messages,
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return ConversationResponse(
        success=True,
        conversation=conversation,
        message=f"Conversation '{conversation.title}' updated successfully",
    )


@router.delete("/{conversation_id}", operation_id="conversation_delete")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation.

    - **conversation_id**: Conversation identifier
    """
    success = conversation_manager.delete_conversation(conversation_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return {
        "success": True,
        "message": f"Conversation '{conversation_id}' deleted successfully",
    }
