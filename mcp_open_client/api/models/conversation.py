"""
Pydantic models for conversation management.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OpenEditor(BaseModel):
    """Open editor for a conversation."""

    file_path: str = Field(..., description="Path to the open file")
    language: Optional[str] = Field(
        None, description="Programming language of the file"
    )
    line_number: Optional[int] = Field(None, description="Current line number")

    model_config = ConfigDict(extra="forbid")


class EnabledTool(BaseModel):
    """Tool enabled for a conversation."""

    server_id: str = Field(..., description="Server UUID or slug")
    tool_name: str = Field(..., description="Name of the tool")

    model_config = ConfigDict(extra="forbid")


class ContextItem(BaseModel):
    """Context item for a conversation."""

    descriptive_name: str = Field(..., description="Descriptive name for this context")
    related_keywords: List[str] = Field(
        default_factory=list, description="Keywords related to this context"
    )
    related_files: List[str] = Field(
        default_factory=list, description="Files related to this context"
    )
    content: str = Field(..., description="Context content")

    model_config = ConfigDict(extra="forbid")


class Message(BaseModel):
    """Message in a conversation."""

    id: str = Field(..., description="Message ID")
    role: str = Field(..., description="Message role (user, assistant, system, tool)")
    content: Optional[str] = Field(None, description="Message content")
    timestamp: str = Field(..., description="Message timestamp")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(
        None, description="Tool calls made by the assistant"
    )
    tool_call_id: Optional[str] = Field(
        None, description="Tool call ID (for tool response messages)"
    )
    name: Optional[str] = Field(
        None, description="Tool name (for tool response messages)"
    )

    model_config = ConfigDict(extra="forbid")


class Conversation(BaseModel):
    """Complete conversation model."""

    id: str = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    description: str = Field(..., description="Conversation description")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    system_prompt: str = Field(
        default="You are a helpful AI assistant.", description="System prompt"
    )
    max_tokens: Optional[int] = Field(
        default=20000,
        description="Maximum tokens for rolling window (None = unlimited)",
    )
    max_messages: Optional[int] = Field(
        default=100,
        description="Maximum number of messages to keep (None = unlimited)",
    )
    enabled_tools: List[EnabledTool] = Field(
        default_factory=list, description="Tools enabled for this conversation"
    )
    open_editors: List[OpenEditor] = Field(
        default_factory=list, description="Open editors in this conversation"
    )
    context: Dict[str, ContextItem] = Field(
        default_factory=dict, description="Context items indexed by ID"
    )
    messages: List[Message] = Field(
        default_factory=list, description="Conversation messages"
    )

    model_config = ConfigDict(extra="forbid")


# Request/Response models


class ConversationCreateRequest(BaseModel):
    """Request to create a new conversation."""

    title: str = Field(..., description="Conversation title")
    description: str = Field(default="", description="Conversation description")
    system_prompt: str = Field(
        default="You are a helpful AI assistant.", description="System prompt"
    )
    max_tokens: Optional[int] = Field(
        default=20000, description="Maximum tokens for rolling window"
    )
    max_messages: Optional[int] = Field(
        default=100, description="Maximum number of messages to keep"
    )

    model_config = ConfigDict(extra="forbid")


class ConversationUpdateRequest(BaseModel):
    """Request to update a conversation."""

    title: Optional[str] = Field(None, description="New title")
    description: Optional[str] = Field(None, description="New description")
    system_prompt: Optional[str] = Field(None, description="New system prompt")
    max_tokens: Optional[int] = Field(
        None, description="Maximum tokens for rolling window"
    )
    max_messages: Optional[int] = Field(
        None, description="Maximum number of messages to keep"
    )

    model_config = ConfigDict(extra="forbid")


class ConversationResponse(BaseModel):
    """Response with conversation data."""

    success: bool = Field(..., description="Whether the operation was successful")
    conversation: Conversation = Field(..., description="Conversation data")
    message: str = Field(..., description="Operation result message")

    model_config = ConfigDict(extra="forbid")


class ConversationListResponse(BaseModel):
    """Response listing conversations."""

    success: bool = Field(..., description="Whether the operation was successful")
    conversations: List[Conversation] = Field(..., description="List of conversations")
    count: int = Field(..., description="Number of conversations")

    model_config = ConfigDict(extra="forbid")


class MessageCreateRequest(BaseModel):
    """Request to add a message to conversation."""

    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")

    model_config = ConfigDict(extra="forbid")


class MessageResponse(BaseModel):
    """Response after adding a message."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: Message = Field(..., description="Created message")
    result_message: str = Field(..., description="Operation result message")

    model_config = ConfigDict(extra="forbid")


class ContextCreateRequest(BaseModel):
    """Request to add context to conversation."""

    descriptive_name: str = Field(..., description="Descriptive name for this context")
    related_keywords: List[str] = Field(
        default_factory=list, description="Keywords related to this context"
    )
    related_files: List[str] = Field(
        default_factory=list, description="Files related to this context"
    )
    content: str = Field(..., description="Context content")

    model_config = ConfigDict(extra="forbid")


class ContextUpdateRequest(BaseModel):
    """Request to update context."""

    descriptive_name: Optional[str] = Field(None, description="New descriptive name")
    related_keywords: Optional[List[str]] = Field(None, description="New keywords")
    related_files: Optional[List[str]] = Field(None, description="New related files")
    content: Optional[str] = Field(None, description="New content")

    model_config = ConfigDict(extra="forbid")


class ContextResponse(BaseModel):
    """Response with context data."""

    success: bool = Field(..., description="Whether the operation was successful")
    context_id: str = Field(..., description="Context item ID")
    context: ContextItem = Field(..., description="Context data")
    message: str = Field(..., description="Operation result message")

    model_config = ConfigDict(extra="forbid")


class EnabledToolCreateRequest(BaseModel):
    """Request to enable a tool for conversation."""

    server_id: str = Field(..., description="Server UUID or slug")
    tool_name: str = Field(..., description="Name of the tool to enable")

    model_config = ConfigDict(extra="forbid")


class EnabledToolResponse(BaseModel):
    """Response after enabling/disabling a tool."""

    success: bool = Field(..., description="Whether the operation was successful")
    enabled_tools: List[EnabledTool] = Field(
        ..., description="Updated list of enabled tools"
    )
    message: str = Field(..., description="Operation result message")

    model_config = ConfigDict(extra="forbid")


class AvailableToolsResponse(BaseModel):
    """Response with available tools from running servers."""

    success: bool = Field(..., description="Whether the operation was successful")
    available_tools: List[Dict[str, Any]] = Field(
        ..., description="List of available tools with server info"
    )
    count: int = Field(..., description="Number of available tools")

    model_config = ConfigDict(extra="forbid")


class ConversationSearchResponse(BaseModel):
    """Response from conversation search."""

    success: bool = Field(..., description="Whether the operation was successful")
    conversations: List[Conversation] = Field(
        ..., description="Conversations matching search"
    )
    count: int = Field(..., description="Number of results")
    message: str = Field(..., description="Operation result message")

    model_config = ConfigDict(extra="forbid")


class OpenEditorCreateRequest(BaseModel):
    """Request to add an open editor to conversation."""

    file_path: str = Field(..., description="Path to the open file")
    language: Optional[str] = Field(
        None, description="Programming language of the file"
    )
    line_number: Optional[int] = Field(None, description="Current line number")

    model_config = ConfigDict(extra="forbid")


class OpenEditorResponse(BaseModel):
    """Response after adding/removing an open editor."""

    success: bool = Field(..., description="Whether the operation was successful")
    open_editors: List[OpenEditor] = Field(
        ..., description="Updated list of open editors"
    )
    message: str = Field(..., description="Operation result message")

    model_config = ConfigDict(extra="forbid")


class ConversationChatRequest(BaseModel):
    """Request to send a message in a conversation."""

    content: str = Field(..., description="User message content")

    model_config = ConfigDict(extra="forbid")


class ConversationChatResponse(BaseModel):
    """Response from conversation chat."""

    success: bool = Field(..., description="Whether the operation was successful")
    user_message: Message = Field(..., description="The user message that was sent")
    assistant_message: Message = Field(..., description="The assistant's response")
    message: str = Field(..., description="Operation result message")
    token_count: int = Field(..., description="Total tokens in conversation context")
    tokens_sent: int = Field(..., description="Tokens sent to LLM in this request")
    messages_in_context: int = Field(
        ..., description="Number of messages included in context"
    )

    model_config = ConfigDict(extra="forbid")
