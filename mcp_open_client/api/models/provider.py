"""
Pydantic models for AI provider management.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ModelConfig(BaseModel):
    """Configuration for an AI model."""

    model_name: str = Field(
        ..., description="Actual model name (e.g., 'gpt-3.5-turbo')"
    )
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for the model")
    description: Optional[str] = Field(None, description="Model description")

    model_config = ConfigDict(
        extra="allow", protected_namespaces=()
    )  # Allow additional fields for future extensions


class ProviderModels(BaseModel):
    """Model configuration for a provider (small and main models)."""

    small: Optional[ModelConfig] = Field(
        None, description="Small/fast model configuration"
    )
    main: Optional[ModelConfig] = Field(
        None, description="Main/powerful model configuration"
    )

    model_config = ConfigDict(extra="allow")


class ProviderConfig(BaseModel):
    """Configuration for an AI provider."""

    name: str = Field(..., description="Provider name")
    base_url: str = Field(..., description="Base API URL")
    api_key: str = Field(..., description="API key for the provider")
    models: ProviderModels = Field(
        default_factory=ProviderModels,
        description="Small and main model configurations",
    )
    enabled: bool = Field(True, description="Whether the provider is enabled")

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v):
        """Ensure base_url ends with trailing slash for consistency."""
        if not v.endswith("/"):
            v += "/"
        return v

    model_config = ConfigDict(
        extra="allow"
    )  # Allow additional provider-specific fields


class ProviderInfo(BaseModel):
    """Complete information about a provider instance."""

    id: str = Field(..., description="Unique provider identifier")
    config: ProviderConfig = Field(..., description="Provider configuration")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    enabled: bool = Field(True, description="Current enabled status")


class ProviderCreateRequest(BaseModel):
    """Request to create a new provider."""

    provider: ProviderConfig = Field(..., description="Provider configuration")


class ProviderCreateResponse(BaseModel):
    """Response after creating a provider."""

    success: bool = Field(..., description="Whether the operation was successful")
    provider: ProviderInfo = Field(..., description="Created provider information")
    message: str = Field(..., description="Operation result message")


class ProviderUpdateRequest(BaseModel):
    """Request to partially update a provider."""

    name: Optional[str] = Field(None, description="Updated provider name")
    base_url: Optional[str] = Field(None, description="Updated base URL")
    api_key: Optional[str] = Field(None, description="Updated API key")
    models: Optional[ProviderModels] = Field(
        None, description="Updated model configurations"
    )
    enabled: Optional[bool] = Field(None, description="Updated enabled status")

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v):
        if v is not None and not v.endswith("/"):
            v += "/"
        return v


class ProviderUpdateResponse(BaseModel):
    """Response after updating a provider."""

    success: bool = Field(..., description="Whether the operation was successful")
    provider: ProviderInfo = Field(..., description="Updated provider information")
    message: str = Field(..., description="Operation result message")


class ProviderListResponse(BaseModel):
    """Response listing all providers."""

    success: bool = Field(..., description="Whether the operation was successful")
    providers: List[ProviderInfo] = Field(..., description="List of all providers")
    count: int = Field(..., description="Number of providers")
    default_provider: Optional[str] = Field(None, description="Default provider ID")


class ModelListResponse(BaseModel):
    """Response listing models for a provider."""

    success: bool = Field(..., description="Whether the operation was successful")
    provider_id: str = Field(..., description="Provider ID")
    models: ProviderModels = Field(
        ..., description="Small and main model configurations"
    )
    count: int = Field(..., description="Number of configured models")


class ModelCreateRequest(BaseModel):
    """Request to add a model to a provider."""

    model_name: str = Field(..., description="Model name")
    config: ModelConfig = Field(..., description="Model configuration")

    model_config = ConfigDict(protected_namespaces=())


class ModelCreateResponse(BaseModel):
    """Response after adding a model."""

    success: bool = Field(..., description="Whether the operation was successful")
    model_name: str = Field(..., description="Added model name")
    provider_id: str = Field(..., description="Provider ID")
    message: str = Field(..., description="Operation result message")

    model_config = ConfigDict(protected_namespaces=())


class ModelUpdateRequest(BaseModel):
    """Request to update a model."""

    config: ModelConfig = Field(..., description="Updated model configuration")


class ModelUpdateResponse(BaseModel):
    """Response after updating a model."""

    success: bool = Field(..., description="Whether the operation was successful")
    model_name: str = Field(..., description="Updated model name")
    provider_id: str = Field(..., description="Provider ID")
    message: str = Field(..., description="Operation result message")

    model_config = ConfigDict(protected_namespaces=())


class ModelSetRequest(BaseModel):
    """Request to set small or main model for a provider."""

    model_type: str = Field(..., description="Model type: 'small' or 'main'")
    config: ModelConfig = Field(..., description="Model configuration")

    model_config = ConfigDict(extra="forbid", protected_namespaces=())


class ModelSetResponse(BaseModel):
    """Response after setting a model."""

    success: bool = Field(..., description="Whether the operation was successful")
    provider_id: str = Field(..., description="Provider ID")
    model_type: str = Field(..., description="Model type that was set")
    model_name: str = Field(..., description="Model name that was set")
    message: str = Field(..., description="Operation result message")

    model_config = ConfigDict(protected_namespaces=())


class ProviderDeleteResponse(BaseModel):
    """Response after deleting a provider."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Operation result message")


class ModelDeleteResponse(BaseModel):
    """Response after deleting a model."""

    success: bool = Field(..., description="Whether the operation was successful")
    model_name: str = Field(..., description="Deleted model name")
    provider_id: str = Field(..., description="Provider ID")
    message: str = Field(..., description="Operation result message")

    model_config = ConfigDict(protected_namespaces=())


class ProviderConfigResponse(BaseModel):
    """Response for global provider configuration."""

    success: bool = Field(..., description="Whether the operation was successful")
    default_provider: Optional[str] = Field(None, description="Default provider ID")
    version: str = Field(..., description="Configuration version")
    updated_at: str = Field(..., description="Last update timestamp")


class ProviderTestRequest(BaseModel):
    """Request to test a provider."""

    model_name: Optional[str] = Field(None, description="Specific model to test")

    model_config = ConfigDict(protected_namespaces=())


class ProviderTestResponse(BaseModel):
    """Response from provider test."""

    success: bool = Field(..., description="Whether the test was successful")
    provider_id: str = Field(..., description="Provider ID that was tested")
    model_name: Optional[str] = Field(None, description="Model that was tested")
    response_time_ms: Optional[float] = Field(
        None, description="Response time in milliseconds"
    )
    available_models: Optional[List[str]] = Field(
        None, description="List of available models"
    )
    error_message: Optional[str] = Field(
        None, description="Error message if test failed"
    )
    message: str = Field(..., description="Test result message")

    model_config = ConfigDict(protected_namespaces=())


class ModelTestRequest(BaseModel):
    """Request to test a specific model."""

    test_message: str = Field("Hello, this is a test.", description="Test message")


class ModelTestResponse(BaseModel):
    """Response from model test."""

    success: bool = Field(..., description="Whether the test was successful")
    provider_id: str = Field(..., description="Provider ID")
    model_name: str = Field(..., description="Model that was tested")
    response_time_ms: Optional[float] = Field(
        None, description="Response time in milliseconds"
    )
    test_response: Optional[str] = Field(None, description="Model response content")
    error_message: Optional[str] = Field(
        None, description="Error message if test failed"
    )
    message: str = Field(..., description="Test result message")

    model_config = ConfigDict(protected_namespaces=())
