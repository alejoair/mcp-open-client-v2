"""
Pydantic models for MCP server configuration and management.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ServerStatus(str, Enum):
    """Server status enumeration."""

    CONFIGURED = "configured"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ServerConfig(BaseModel):
    """Configuration for an MCP server."""

    name: str = Field(..., description="Unique name for the server")
    transport: str = Field(
        default="stdio", description="Transport type (currently only 'stdio' supported)"
    )
    command: str = Field(..., description="Command to execute for the server")
    args: List[str] = Field(default_factory=list, description="Command line arguments")
    env: Optional[Dict[str, str]] = Field(
        default=None, description="Environment variables"
    )
    cwd: Optional[str] = Field(default=None, description="Working directory")

    model_config = ConfigDict(extra="forbid")


class ServerInfo(BaseModel):
    """Information about a server instance."""

    id: str = Field(..., description="Unique server identifier")
    config: ServerConfig = Field(..., description="Server configuration")
    status: ServerStatus = Field(
        default=ServerStatus.CONFIGURED, description="Current server status"
    )
    created_at: str = Field(..., description="Timestamp when server was created")
    started_at: Optional[str] = Field(
        None, description="Timestamp when server was started"
    )
    stopped_at: Optional[str] = Field(
        None, description="Timestamp when server was stopped"
    )
    error_message: Optional[str] = Field(None, description="Last error message if any")
    process_id: Optional[int] = Field(None, description="Process ID if running")

    model_config = ConfigDict(extra="forbid")


class ServerCreateRequest(BaseModel):
    """Request to create a new server."""

    server: ServerConfig = Field(..., description="Server configuration")

    model_config = ConfigDict(extra="forbid")


class ServerCreateResponse(BaseModel):
    """Response after creating a server."""

    success: bool = Field(..., description="Whether the operation was successful")
    server: ServerInfo = Field(..., description="Created server information")
    message: str = Field(..., description="Operation result message")


class ServerListResponse(BaseModel):
    """Response listing all servers."""

    success: bool = Field(..., description="Whether the operation was successful")
    servers: List[ServerInfo] = Field(..., description="List of all servers")
    count: int = Field(..., description="Number of servers")


class ServerStartResponse(BaseModel):
    """Response after starting a server."""

    success: bool = Field(..., description="Whether the operation was successful")
    server: ServerInfo = Field(..., description="Updated server information")
    message: str = Field(..., description="Operation result message")


class ServerStopResponse(BaseModel):
    """Response after stopping a server."""

    success: bool = Field(..., description="Whether the operation was successful")
    server: ServerInfo = Field(..., description="Updated server information")
    message: str = Field(..., description="Operation result message")


class ToolInfo(BaseModel):
    """Information about an MCP tool."""

    name: str = Field(..., description="Tool name")
    description: Optional[str] = Field(None, description="Tool description")
    input_schema: Optional[Dict[str, Any]] = Field(
        None, description="JSON schema for tool input"
    )

    model_config = ConfigDict(extra="forbid")


class ServerToolsResponse(BaseModel):
    """Response with server tools."""

    success: bool = Field(..., description="Whether the operation was successful")
    server_name: str = Field(..., description="Server name")
    status: ServerStatus = Field(..., description="Current server status")
    tools: List[ToolInfo] = Field(..., description="List of available tools")
    message: str = Field(..., description="Operation result message")


class ToolCallRequest(BaseModel):
    """Request to call a tool."""

    tool_name: str = Field(..., description="Name of the tool to call")
    arguments: Optional[Dict[str, Any]] = Field(
        default=None, description="Tool arguments as key-value pairs"
    )

    model_config = ConfigDict(extra="forbid")


class ToolCallResponse(BaseModel):
    """Response after calling a tool."""

    success: bool = Field(..., description="Whether the operation was successful")
    server_id: str = Field(..., description="Server identifier")
    server_name: str = Field(..., description="Server name")
    tool_name: str = Field(..., description="Tool that was called")
    result: Any = Field(..., description="Tool execution result")
    message: str = Field(..., description="Operation result message")


class ErrorResponse(BaseModel):
    """Error response."""

    success: bool = Field(default=False, description="Always False for error responses")
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )

    model_config = ConfigDict(extra="forbid")
