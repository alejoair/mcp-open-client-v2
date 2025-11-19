"""
AI Provider Manager - Main orchestrator for provider management.
"""

from typing import Dict, Optional

from ...api.models.provider import (
    ModelConfig,
    ModelCreateResponse,
    ModelDeleteResponse,
    ModelListResponse,
    ModelSetResponse,
    ModelUpdateResponse,
    ProviderConfig,
    ProviderConfigResponse,
    ProviderCreateResponse,
    ProviderDeleteResponse,
    ProviderInfo,
    ProviderListResponse,
    ProviderUpdateResponse,
)
from ...config import ensure_config_directory, get_config_path
from ...exceptions import MCPError
from ..provider_validator import AIProviderValidator, ModelTestResult, ValidationResult
from .model_operations import ModelOperations
from .provider_operations import ProviderOperations
from .storage import ProviderStorage


class AIProviderManager:
    """
    Manages AI provider configurations with JSON persistence.

    This is the main class that orchestrates provider and model operations
    by delegating to specialized components.
    """

    def __init__(self, config_file: str = "ai_providers.json"):
        """
        Initialize AI provider manager.

        Args:
            config_file: Path to JSON configuration file (relative to user config dir)
        """
        # Shared state
        self._providers: Dict[str, ProviderInfo] = {}
        self._default_provider_ref = [None]  # Use list for mutable reference

        # Components
        self._validator = AIProviderValidator()

        # Ensure config directory exists and get config file path
        ensure_config_directory()
        config_file_path = get_config_path(config_file)

        # Initialize storage and load data
        self._storage = ProviderStorage(config_file_path)
        self._providers, self._default_provider_ref[0] = self._storage.load_providers()

        # Initialize operations with shared state and save callback
        self._provider_ops = ProviderOperations(
            self._providers, self._default_provider_ref, self._save_providers
        )
        self._model_ops = ModelOperations(self._providers, self._save_providers)

    def _save_providers(self) -> None:
        """
        Save provider configurations to storage.
        """
        self._storage.save_providers(self._providers, self._default_provider_ref[0])

    # Provider operations - delegate to ProviderOperations

    async def add_provider(self, config: ProviderConfig) -> ProviderCreateResponse:
        """Add a new AI provider configuration."""
        return await self._provider_ops.add_provider(config)

    def get_provider(self, provider_id: str) -> Optional[ProviderInfo]:
        """Get provider information by ID."""
        return self._provider_ops.get_provider(provider_id)

    def get_all_providers(self) -> ProviderListResponse:
        """Get all provider information."""
        return self._provider_ops.get_all_providers()

    def find_provider_by_name(self, name: str) -> Optional[ProviderInfo]:
        """Find provider by name."""
        return self._provider_ops.find_provider_by_name(name)

    def get_default_provider(self) -> Optional[ProviderInfo]:
        """Get the default provider."""
        return self._provider_ops.get_default_provider()

    async def update_provider(
        self, provider_id: str, config: ProviderConfig
    ) -> ProviderUpdateResponse:
        """Update a provider configuration completely."""
        return await self._provider_ops.update_provider(provider_id, config)

    async def delete_provider(self, provider_id: str) -> ProviderDeleteResponse:
        """Delete a provider configuration."""
        return await self._provider_ops.delete_provider(provider_id)

    async def set_default_provider(self, provider_id: str) -> bool:
        """Set a provider as the default."""
        return await self._provider_ops.set_default_provider(provider_id)

    async def enable_provider(self, provider_id: str) -> bool:
        """Enable a provider."""
        return await self._provider_ops.enable_provider(provider_id)

    async def disable_provider(self, provider_id: str) -> bool:
        """Disable a provider."""
        return await self._provider_ops.disable_provider(provider_id)

    def get_config(self) -> ProviderConfigResponse:
        """Get global configuration."""
        return self._provider_ops.get_config()

    # Model operations - delegate to ModelOperations

    async def add_model(
        self, provider_id: str, model_name: str, config: ModelConfig
    ) -> ModelCreateResponse:
        """Add a model to a provider (legacy method)."""
        return await self._model_ops.add_model(provider_id, model_name, config)

    async def update_model(
        self, provider_id: str, model_name: str, config: ModelConfig
    ) -> ModelUpdateResponse:
        """Update a model configuration (legacy method)."""
        return await self._model_ops.update_model(provider_id, model_name, config)

    async def delete_model(
        self, provider_id: str, model_name: str
    ) -> ModelDeleteResponse:
        """Delete a model from a provider (legacy method)."""
        return await self._model_ops.delete_model(provider_id, model_name)

    def get_provider_models(self, provider_id: str) -> ModelListResponse:
        """Get configured models (small and main) for a provider."""
        return self._model_ops.get_provider_models(provider_id)

    async def set_model(
        self, provider_id: str, model_type: str, model_config: ModelConfig
    ) -> ModelSetResponse:
        """Set a small or main model for a provider."""
        return await self._model_ops.set_model(provider_id, model_type, model_config)

    async def remove_model(
        self, provider_id: str, model_type: str
    ) -> ModelDeleteResponse:
        """Remove a small or main model from a provider."""
        return await self._model_ops.remove_model(provider_id, model_type)

    # Validation operations

    async def validate_provider(
        self, provider_id: str, model_name: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate a provider connection and optionally test a specific model.

        Args:
            provider_id: Provider identifier
            model_name: Optional specific model to test

        Returns:
            ValidationResult: Validation results
        """
        provider = self._providers.get(provider_id)
        if not provider:
            raise MCPError(f"Provider with ID '{provider_id}' not found")

        return await self._validator.validate_provider(provider.config, model_name)

    async def test_model(
        self,
        provider_id: str,
        model_name: str,
        test_message: str = "Hello, this is a test.",
    ) -> ModelTestResult:
        """
        Test a specific model with a simple message.

        Args:
            provider_id: Provider identifier
            model_name: Model to test
            test_message: Test message to send

        Returns:
            ModelTestResult: Test results
        """
        provider = self._providers.get(provider_id)
        if not provider:
            raise MCPError(f"Provider with ID '{provider_id}' not found")

        return await self._validator.test_model(
            provider.config, model_name, test_message
        )
