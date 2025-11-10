"""
AI Provider Manager - Manages AI provider configurations with JSON persistence.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..api.models.provider import (
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
from ..exceptions import MCPError
from .provider_validator import AIProviderValidator, ModelTestResult, ValidationResult


class AIProviderManager:
    """Manages AI provider configurations with JSON persistence."""

    def __init__(self, config_file: str = "ai_providers.json"):
        """
        Initialize AI provider manager.

        Args:
            config_file: Path to JSON configuration file
        """
        self._providers: Dict[str, ProviderInfo] = {}
        self._config_file = Path(config_file)
        self._default_provider: Optional[str] = None
        self._validator = AIProviderValidator()
        self._load_providers()

    def _load_providers(self) -> None:
        """
        Load provider configurations from JSON file.
        """
        if not self._config_file.exists():
            return

        try:
            with open(self._config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            providers_data = data.get("providers", [])
            for provider_data in providers_data:
                config_data = provider_data.get("config")
                if config_data:
                    config = ProviderConfig(**config_data)

                    provider_info = ProviderInfo(
                        id=provider_data["id"],
                        config=config,
                        created_at=provider_data.get(
                            "created_at", datetime.utcnow().isoformat()
                        ),
                        updated_at=provider_data.get("updated_at"),
                        enabled=provider_data.get("enabled", True),
                    )

                    self._providers[provider_info.id] = provider_info

            # Load default provider
            self._default_provider = data.get("default_provider")

        except Exception as e:
            # If loading fails, start with empty provider list
            print(
                f"Warning: Failed to load provider configurations from {self._config_file}: {e}"
            )
            self._providers = {}
            self._default_provider = None

    def _save_providers(self) -> None:
        """
        Save provider configurations to JSON file.
        """
        try:
            # Convert providers to dict format
            providers_data = []
            for provider_id, provider in self._providers.items():
                provider_dict = {
                    "id": provider.id,
                    "config": {
                        "name": provider.config.name,
                        "base_url": provider.config.base_url,
                        "api_key": provider.config.api_key,
                        "models": {
                            "small": (
                                provider.config.models.small.model_dump()
                                if provider.config.models.small
                                else None
                            ),
                            "main": (
                                provider.config.models.main.model_dump()
                                if provider.config.models.main
                                else None
                            ),
                        },
                        "enabled": provider.config.enabled,
                    },
                    "created_at": provider.created_at,
                    "updated_at": provider.updated_at,
                    "enabled": provider.enabled,
                }
                providers_data.append(provider_dict)

            # Save to file
            data = {
                "providers": providers_data,
                "version": "1.0",
                "default_provider": self._default_provider,
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Create directory if it doesn't exist
            self._config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(
                f"Warning: Failed to save provider configurations to {self._config_file}: {e}"
            )

    async def add_provider(self, config: ProviderConfig) -> ProviderCreateResponse:
        """
        Add a new AI provider configuration.

        Args:
            config: Provider configuration

        Returns:
            ProviderCreateResponse: Created provider information
        """
        # Check for duplicate names
        for provider in self._providers.values():
            if provider.config.name == config.name:
                raise MCPError(f"Provider with name '{config.name}' already exists")

        # Generate unique ID
        provider_id = str(uuid.uuid4())

        # Create provider info
        provider_info = ProviderInfo(
            id=provider_id,
            config=config,
            created_at=datetime.utcnow().isoformat(),
            enabled=config.enabled,
        )

        self._providers[provider_id] = provider_info

        # Set as default if it's the first provider
        if self._default_provider is None:
            self._default_provider = provider_id

        # Save to JSON file
        self._save_providers()

        return ProviderCreateResponse(
            success=True,
            provider=provider_info,
            message=f"Provider '{config.name}' created successfully with ID: {provider_id}",
        )

    def get_provider(self, provider_id: str) -> Optional[ProviderInfo]:
        """
        Get provider information by ID.

        Args:
            provider_id: Provider identifier

        Returns:
            ProviderInfo or None if not found
        """
        return self._providers.get(provider_id)

    def get_all_providers(self) -> ProviderListResponse:
        """
        Get all provider information.

        Returns:
            ProviderListResponse: List of all providers
        """
        providers = list(self._providers.values())
        return ProviderListResponse(
            success=True,
            providers=providers,
            count=len(providers),
            default_provider=self._default_provider,
        )

    def find_provider_by_name(self, name: str) -> Optional[ProviderInfo]:
        """
        Find provider by name.

        Args:
            name: Provider name

        Returns:
            ProviderInfo or None if not found
        """
        for provider in self._providers.values():
            if provider.config.name == name:
                return provider
        return None

    def get_default_provider(self) -> Optional[ProviderInfo]:
        """
        Get the default provider.

        Returns:
            ProviderInfo or None if no default is set
        """
        if self._default_provider:
            return self._providers.get(self._default_provider)
        return None

    async def update_provider(
        self, provider_id: str, config: ProviderConfig
    ) -> ProviderUpdateResponse:
        """
        Update a provider configuration completely.

        Args:
            provider_id: Provider identifier
            config: Updated provider configuration

        Returns:
            ProviderUpdateResponse: Updated provider information
        """
        provider = self._providers.get(provider_id)
        if not provider:
            raise MCPError(f"Provider with ID '{provider_id}' not found")

        # Check for duplicate names (excluding this provider)
        for other_provider in self._providers.values():
            if (
                other_provider.id != provider_id
                and other_provider.config.name == config.name
            ):
                raise MCPError(f"Provider with name '{config.name}' already exists")

        # Update provider
        old_config = provider.config
        provider.config = config
        provider.updated_at = datetime.utcnow().isoformat()

        # Save to JSON file
        self._save_providers()

        return ProviderUpdateResponse(
            success=True,
            provider=provider,
            message=f"Provider '{config.name}' updated successfully",
        )

    async def delete_provider(self, provider_id: str) -> ProviderDeleteResponse:
        """
        Delete a provider configuration.

        Args:
            provider_id: Provider identifier

        Returns:
            ProviderDeleteResponse: Confirmation of deletion
        """
        provider = self._providers.get(provider_id)
        if not provider:
            raise MCPError(f"Provider with ID '{provider_id}' not found")

        provider_name = provider.config.name
        del self._providers[provider_id]

        # Update default provider if necessary
        if self._default_provider == provider_id:
            self._default_provider = None
            # Set new default if there are other providers
            if self._providers:
                self._default_provider = next(iter(self._providers.keys()))

        # Save to JSON file
        self._save_providers()

        return ProviderDeleteResponse(
            success=True, message=f"Provider '{provider_name}' deleted successfully"
        )

    async def add_model(
        self, provider_id: str, model_name: str, config: ModelConfig
    ) -> ModelCreateResponse:
        """
        Add a model to a provider.

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
        self._save_providers()

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
        Update a model configuration.

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
        self._save_providers()

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
        Delete a model from a provider.

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
        self._save_providers()

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
        self._save_providers()

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
        self._save_providers()

        return ModelDeleteResponse(
            success=True,
            model_name=model_name,
            provider_id=provider_id,
            message=f"{model_type.capitalize()} model '{model_name}' removed from provider '{provider.config.name}' successfully",
        )

    async def set_default_provider(self, provider_id: str) -> bool:
        """
        Set a provider as the default.

        Args:
            provider_id: Provider identifier

        Returns:
            True if successful
        """
        provider = self._providers.get(provider_id)
        if not provider:
            raise MCPError(f"Provider with ID '{provider_id}' not found")

        self._default_provider = provider_id
        self._save_providers()

        return True

    async def enable_provider(self, provider_id: str) -> bool:
        """
        Enable a provider.

        Args:
            provider_id: Provider identifier

        Returns:
            True if successful
        """
        provider = self._providers.get(provider_id)
        if not provider:
            raise MCPError(f"Provider with ID '{provider_id}' not found")

        provider.enabled = True
        provider.config.enabled = True
        provider.updated_at = datetime.utcnow().isoformat()

        self._save_providers()

        return True

    async def disable_provider(self, provider_id: str) -> bool:
        """
        Disable a provider.

        Args:
            provider_id: Provider identifier

        Returns:
            True if successful
        """
        provider = self._providers.get(provider_id)
        if not provider:
            raise MCPError(f"Provider with ID '{provider_id}' not found")

        provider.enabled = False
        provider.config.enabled = False
        provider.updated_at = datetime.utcnow().isoformat()

        # Update default provider if this was the default
        if self._default_provider == provider_id:
            # Find another enabled provider to be the default
            for pid, p in self._providers.items():
                if pid != provider_id and p.enabled:
                    self._default_provider = pid
                    break
            else:
                self._default_provider = None

        self._save_providers()

        return True

    def get_config(self) -> ProviderConfigResponse:
        """
        Get global configuration.

        Returns:
            ProviderConfigResponse: Global configuration
        """
        return ProviderConfigResponse(
            success=True,
            default_provider=self._default_provider,
            version="1.0",
            updated_at=datetime.utcnow().isoformat(),
        )

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
