"""
Pydantic models for MCP Registry responses.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RegistryServerInfo(BaseModel):
    """Information about a server from the MCP registry."""

    name: str = Field(..., description="Server name (e.g., 'ai.exa/exa')")
    description: Optional[str] = Field(None, description="Server description")
    version: Optional[str] = Field(None, description="Server version")
    repository_url: Optional[str] = Field(None, description="Repository URL")
    published_at: Optional[str] = Field(None, description="Publication timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    transport_types: List[str] = Field(
        default_factory=list, description="Available transport types"
    )
    full_data: Optional[Dict[str, Any]] = Field(
        None, description="Complete server data from registry"
    )

    model_config = ConfigDict(extra="forbid")


class RegistrySearchResponse(BaseModel):
    """Response from registry search."""

    success: bool = Field(..., description="Whether the operation was successful")
    servers: List[RegistryServerInfo] = Field(..., description="List of servers found")
    count: int = Field(..., description="Number of servers returned")
    total: Optional[int] = Field(None, description="Total servers available")
    message: str = Field(..., description="Operation result message")


class RegistryServerDetailResponse(BaseModel):
    """Response with detailed server information."""

    success: bool = Field(..., description="Whether the operation was successful")
    server: Optional[RegistryServerInfo] = Field(None, description="Server information")
    message: str = Field(..., description="Operation result message")


class RegistryCategoriesResponse(BaseModel):
    """Response with server categories/namespaces."""

    success: bool = Field(..., description="Whether the operation was successful")
    categories: Dict[str, List[str]] = Field(
        ..., description="Categories mapping to server names"
    )
    count: int = Field(..., description="Number of categories")
    message: str = Field(..., description="Operation result message")


class RegistryHealthResponse(BaseModel):
    """Response from registry health check."""

    success: bool = Field(..., description="Whether the registry is healthy")
    status: str = Field(..., description="Health status")
    message: str = Field(..., description="Status message")
