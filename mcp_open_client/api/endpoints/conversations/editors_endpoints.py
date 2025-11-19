"""
Open editor endpoints for conversations.
"""

from fastapi import HTTPException, Query, status

from ...models.conversation import OpenEditorCreateRequest, OpenEditorResponse
from . import router
from .dependencies import conversation_manager


@router.get("/{conversation_id}/editors", operation_id="conversation_get_open_editors")
async def get_open_editors(conversation_id: str):
    """
    Get all open editors for a conversation.

    - **conversation_id**: Conversation identifier
    """
    editors = conversation_manager.get_open_editors(conversation_id)
    if editors is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return {"success": True, "open_editors": editors, "count": len(editors)}


@router.post(
    "/{conversation_id}/editors",
    response_model=OpenEditorResponse,
    operation_id="conversation_add_open_editor",
)
async def add_open_editor(conversation_id: str, request: OpenEditorCreateRequest):
    """
    Add an open editor to a conversation.

    - **conversation_id**: Conversation identifier
    - **file_path**: Path to the open file
    - **language**: Optional programming language
    - **line_number**: Optional current line number
    """
    # Check if conversation exists
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    # Add the editor
    open_editors = conversation_manager.add_open_editor(
        conversation_id=conversation_id,
        file_path=request.file_path,
        language=request.language,
        line_number=request.line_number,
    )

    return OpenEditorResponse(
        success=True,
        open_editors=open_editors,
        message=f"Editor '{request.file_path}' added successfully",
    )


@router.delete(
    "/{conversation_id}/editors",
    response_model=OpenEditorResponse,
    operation_id="conversation_remove_open_editor",
)
async def remove_open_editor(
    conversation_id: str,
    file_path: str = Query(..., description="Path to the open file"),
):
    """
    Remove an open editor from a conversation.

    - **conversation_id**: Conversation identifier
    - **file_path**: Path to the open file to remove
    """
    open_editors = conversation_manager.remove_open_editor(
        conversation_id=conversation_id, file_path=file_path
    )

    if open_editors is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return OpenEditorResponse(
        success=True,
        open_editors=open_editors,
        message=f"Editor '{file_path}' removed",
    )


# Chat endpoint
