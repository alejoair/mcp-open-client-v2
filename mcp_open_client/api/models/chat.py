"""
Pydantic models for OpenAI-compatible chat endpoint with provider support.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class Role(str, Enum):
    """Message role enumeration."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ModelType(str, Enum):
    """Model type enumeration for provider selection."""

    SMALL = "small"
    MAIN = "main"


class ToolCall(BaseModel):
    """Tool call for OpenAI-compatible function calling."""

    id: str = Field(..., description="Unique identifier for the tool call")
    type: str = Field(default="function", description="Type of tool call")
    function: Dict[str, Any] = Field(..., description="Function call details")


class Function(BaseModel):
    """Function definition for tool calling."""

    name: str = Field(..., description="Name of the function")
    description: Optional[str] = Field(None, description="Description of the function")
    parameters: Dict[str, Any] = Field(
        ..., description="JSON schema for function parameters"
    )


class Message(BaseModel):
    """Chat message in OpenAI format."""

    role: Role = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")
    name: Optional[str] = Field(None, description="Name of the participant")
    tool_calls: Optional[List[ToolCall]] = Field(
        None, description="Tool calls in the message"
    )
    tool_call_id: Optional[str] = Field(
        None, description="ID of the tool call this message responds to"
    )

    model_config = ConfigDict(extra="allow")


class ChatFunction(BaseModel):
    """Function definition for chat completion."""

    name: str = Field(..., description="Name of the function")
    description: Optional[str] = Field(None, description="Description of the function")
    parameters: Dict[str, Any] = Field(
        ..., description="JSON schema for function parameters"
    )


class ChatRequest(BaseModel):
    """Request model for OpenAI-compatible chat endpoint."""

    model: str = Field(..., description="Model name (will be resolved to small/main)")
    messages: List[Message] = Field(
        ..., description="List of messages in the conversation"
    )
    model_type: Optional[ModelType] = Field(
        None, description="Model type: 'small' or 'main'"
    )
    max_tokens: Optional[int] = Field(
        None, description="Maximum number of tokens to generate"
    )
    temperature: Optional[float] = Field(1.0, description="Sampling temperature")
    top_p: Optional[float] = Field(1.0, description="Nucleus sampling probability")
    n: Optional[int] = Field(1, description="Number of completions to generate")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")
    logprobs: Optional[bool] = Field(
        None, description="Whether to return log probabilities"
    )
    top_logprobs: Optional[int] = Field(
        None, description="Number of top log probabilities to return"
    )
    echo: Optional[bool] = Field(None, description="Whether to echo the prompt")
    stop: Optional[Union[str, List[str]]] = Field(None, description="Stop sequences")
    presence_penalty: Optional[float] = Field(0.0, description="Presence penalty")
    frequency_penalty: Optional[float] = Field(0.0, description="Frequency penalty")
    best_of: Optional[int] = Field(
        None, description="Number of completions to generate server-side"
    )
    logit_bias: Optional[Dict[str, float]] = Field(
        None, description="Logit bias adjustments"
    )
    user: Optional[str] = Field(None, description="User identifier")
    functions: Optional[List[ChatFunction]] = Field(
        None, description="Available functions"
    )
    function_call: Optional[Union[str, Dict[str, str]]] = Field(
        None, description="Function call to make"
    )
    provider: Optional[str] = Field(None, description="Override provider name")
    api_key: Optional[str] = Field(None, description="Override API key")
    base_url: Optional[str] = Field(None, description="Override base URL")

    model_config = ConfigDict(extra="allow", protected_namespaces=())


class ChatCompletionTokenLogprob(BaseModel):
    """Token log probability information."""

    token: str = Field(..., description="Token")
    logprob: float = Field(..., description="Log probability of the token")
    bytes: Optional[List[int]] = Field(None, description="Token bytes")

    model_config = ConfigDict(extra="allow")


class ChatCompletionLogprobsContent(BaseModel):
    """Log probabilities content."""

    tokens: List[str] = Field(..., description="Tokens")
    token_logprobs: List[float] = Field(..., description="Log probabilities of tokens")
    top_logprobs: Optional[List[Dict[str, Any]]] = Field(
        None, description="Top log probabilities"
    )
    text_offset: List[int] = Field(..., description="Text offsets")

    model_config = ConfigDict(extra="allow")


class ChatCompletionLogprobs(BaseModel):
    """Log probabilities for a completion choice."""

    content: List[ChatCompletionLogprobsContent] = Field(
        ..., description="Log probability content"
    )

    model_config = ConfigDict(extra="allow")


class FunctionCall(BaseModel):
    """Function call in completion."""

    name: str = Field(..., description="Name of the function")
    arguments: str = Field(..., description="Arguments for the function")

    model_config = ConfigDict(extra="allow")


class Choice(BaseModel):
    """Completion choice."""

    message: Message = Field(..., description="Generated message")
    finish_reason: Optional[str] = Field(None, description="Reason for finishing")
    index: int = Field(..., description="Choice index")
    logprobs: Optional[ChatCompletionLogprobs] = Field(
        None, description="Log probabilities"
    )

    model_config = ConfigDict(extra="allow")


class Usage(BaseModel):
    """Token usage statistics."""

    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(
        ..., description="Number of tokens in the completion"
    )
    total_tokens: int = Field(..., description="Total number of tokens")

    model_config = ConfigDict(extra="allow")


class ChatResponse(BaseModel):
    """Response model for OpenAI-compatible chat endpoint."""

    id: str = Field(..., description="Unique identifier for the chat completion")
    object: str = Field(default="chat.completion", description="Object type")
    created: int = Field(..., description="Unix timestamp of creation")
    model: str = Field(..., description="Model used for completion")
    choices: List[Choice] = Field(..., description="Completion choices")
    usage: Optional[Usage] = Field(None, description="Token usage statistics")
    system_fingerprint: Optional[str] = Field(None, description="System fingerprint")

    model_config = ConfigDict(extra="allow")


class StreamChatResponse(BaseModel):
    """Streaming response chunk for chat completion."""

    id: str = Field(..., description="Unique identifier for the chat completion")
    object: str = Field(default="chat.completion.chunk", description="Object type")
    created: int = Field(..., description="Unix timestamp of creation")
    model: str = Field(..., description="Model used for completion")
    choices: List[Dict[str, Any]] = Field(..., description="Completion choices")
    system_fingerprint: Optional[str] = Field(None, description="System fingerprint")

    model_config = ConfigDict(extra="allow")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: Dict[str, Any] = Field(..., description="Error information")

    model_config = ConfigDict(extra="allow")
