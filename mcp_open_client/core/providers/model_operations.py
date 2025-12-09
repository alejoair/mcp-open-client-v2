"""
Model operations - Model management for AI providers.
"""

from datetime import datetime
from typing import Callable, Dict

from ...api.models.provider import (
    ModelConfig,
    ModelCreateResponse,
    ModelDeleteResponse,
    ModelListResponse,
    ModelSetResponse,
    ModelUpdateResponse,
    ProviderInfo,
)
from ...exceptions import MCPError


class ModelOperations:
    """Handles model management operations for providers."""

    def __init__(
        self, providers: Dict[str, ProviderInfo], save_callback: Callable[[], None]
    ):
        """
        Initialize model operations.

        Args:
            providers: Dictionary of provider information (shared reference)
            save_callback: Callback to save providers to storage
        """
        self._providers = providers
        self._save = save_callback

    async def add_model(
        self, provider_id: str, model_name: str, config: ModelConfig
    ) -> ModelCreateResponse:
        """
        Add a model to a provider (legacy method).

        Args:
            provider_id: Provider identifier
            model_name: Model name
            config: Model configuration

        Returns:
            ModelCreateResponse: Confirmation of model addition
        """
        provider = self._providers.get(provider_id)
        if not provider:
            raise MCPError(f"Provider with ID '{provider_id}' not found")

        if model_name in provider.config.models:
            raise MCPError(
                f"Model '{model_name}' already exists for provider '{provider.config.name}'"
            )

        provider.config.models[model_name] = config
        provider.updated_at = datetime.utcnow().isoformat()

        # Save to JSON file
        self._save()

        return ModelCreateResponse(
            success=True,
            model_name=model_name,
            provider_id=provider_id,
            message=f"Model '{model_name}' added to provider '{provider.config.name}' successfully",
        )

    async def update_model(
        self, provider_id: str, model_name: str, config: ModelConfig
    ) -> ModelUpdateResponse:
        """
        Update a model configuration (legacy method).

        Args:
            provider_id: Provider identifier
            model_name: Model name
            config: Updated model configuration

        Returns:
            ModelUpdateResponse: Confirmation of model update
        """
        provider = self._providers.get(provider_id)
        if not provider:
            raise MCPError(f"Provider with ID '{provider_id}' not found")

        if model_name not in provider.config.models:
            raise MCPError(
                f"Model '{model_name}' not found for provider '{provider.config.name}'"
            )

        provider.config.models[model_name] = config
        provider.updated_at = datetime.utcnow().isoformat()

        # Save to JSON file
        self._save()

        return ModelUpdateResponse(
            success=True,
            model_name=model_name,
            provider_id=provider_id,
            message=f"Model '{model_name}' updated for provider '{provider.config.name}' successfully",
        )

    async def delete_model(
        self, provider_id: str, model_name: str
    ) -> ModelDeleteResponse:
        """
        Delete a model from a provider (legacy method).

        Args:
            provider_id: Provider identifier
            model_name: Model name

        Returns:
            ModelDeleteResponse: Confirmation of model deletion
        """
        provider = self._providers.get(provider_id)
        if not provider:
            raise MCPError(f"Provider with ID '{provider_id}' not found")

        if model_name not in provider.config.models:
            raise MCPError(
                f"Model '{model_name}' not found for provider '{provider.config.name}'"
            )

        del provider.config.models[model_name]
        provider.updated_at = datetime.utcnow().isoformat()

        # Save to JSON file
        self._save()

        return ModelDeleteResponse(
            success=True,
            model_name=model_name,
            provider_id=provider_id,
            message=f"Model '{model_name}' deleted from provider '{provider.config.name}' successfully",
        )

    def get_provider_models(self, provider_id: str) -> ModelListResponse:
        """
        Get configured models (small and main) for a provider.

        Args:
            provider_id: Provider identifier

        Returns:
            ModelListResponse: Small and main models for the provider
        """
        provider = self._providers.get(provider_id)
        if not provider:
            raise MCPError(f"Provider with ID '{provider_id}' not found")

        # Count configured models
        count = 0
        if provider.config.models.small:
            count += 1
        if provider.config.models.main:
            count += 1

        return ModelListResponse(
            success=True,
            provider_id=provider_id,
            models=provider.config.models,
            count=count,
        )

    async def set_model(
        self, provider_id: str, model_type: str, model_config: ModelConfig
    ) -> ModelSetResponse:
        """
        Set a small or main model for a provider.

        Args:
            provider_id: Provider identifier
            model_type: Model type ('small' or 'main')
            model_config: Model configuration

        Returns:
            ModelSetResponse: Confirmation of model setting
        """
        provider = self._providers.get(provider_id)
        if not provider:
            raise MCPError(f"Provider with ID '{provider_id}' not found")

        if model_type not in ["small", "main"]:
            raise MCPError(
                f"Invalid model type '{model_type}'. Must be 'small' or 'main'"
            )

        # Set the model
        if model_type == "small":
            provider.config.models.small = model_config
        else:  # model_type == 'main'
            provider.config.models.main = model_config

        provider.updated_at = datetime.utcnow().isoformat()

        # Save to JSON file
        self._save()

        return ModelSetResponse(
            success=True,
            provider_id=provider_id,
            model_type=model_type,
            model_name=model_config.model_name,
            message=f"{model_type.capitalize()} model '{model_config.model_name}' set for provider '{provider.config.name}' successfully",
        )

    async def remove_model(
        self, provider_id: str, model_type: str
    ) -> ModelDeleteResponse:
        """
        Remove a small or main model from a provider.

        Args:
            provider_id: Provider identifier
            model_type: Model type ('small' or 'main')

        Returns:
            ModelDeleteResponse: Confirmation of model removal
        """
        provider = self._providers.get(provider_id)
        if not provider:
            raise MCPError(f"Provider with ID '{provider_id}' not found")

        if model_type not in ["small", "main"]:
            raise MCPError(
                f"Invalid model type '{model_type}'. Must be 'small' or 'main'"
            )

        # Check if model exists
        if model_type == "small" and not provider.config.models.small:
            raise MCPError(
                f"No small model configured for provider '{provider.config.name}'"
            )
        elif model_type == "main" and not provider.config.models.main:
            raise MCPError(
                f"No main model configured for provider '{provider.config.name}'"
            )

        # Get model name before removal
        model_name = None
        if model_type == "small" and provider.config.models.small:
            model_name = provider.config.models.small.model_name
            provider.config.models.small = None
        elif model_type == "main" and provider.config.models.main:
            model_name = provider.config.models.main.model_name
            provider.config.models.main = None

        provider.updated_at = datetime.utcnow().isoformat()

        # Save to JSON file
        self._save()

        return ModelDeleteResponse(
            success=True,
            model_name=model_name,
            provider_id=provider_id,
            message=f"{model_type.capitalize()} model '{model_name}' removed from provider '{provider.config.name}' successfully",
        )
