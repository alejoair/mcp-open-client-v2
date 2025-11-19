"""
Provider operations - CRUD and management for AI providers.
"""

import uuid
from datetime import datetime
from typing import Callable, Dict, Optional

from ...api.models.provider import (
    ProviderConfig,
    ProviderConfigResponse,
    ProviderCreateResponse,
    ProviderDeleteResponse,
    ProviderInfo,
    ProviderListResponse,
    ProviderUpdateResponse,
)
from ...exceptions import MCPError


class ProviderOperations:
    """Handles provider CRUD operations and default management."""

    def __init__(
        self,
        providers: Dict[str, ProviderInfo],
        default_provider_ref: list,
        save_callback: Callable[[], None],
    ):
        """
        Initialize provider operations.

        Args:
            providers: Dictionary of provider information (shared reference)
            default_provider_ref: List containing default provider ID (shared reference)
            save_callback: Callback to save providers to storage
        """
        self._providers = providers
        self._default_provider_ref = default_provider_ref
        self._save = save_callback

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
        if self._default_provider_ref[0] is None:
            self._default_provider_ref[0] = provider_id

        # Save to JSON file
        self._save()

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
            default_provider=self._default_provider_ref[0],
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
        if self._default_provider_ref[0]:
            return self._providers.get(self._default_provider_ref[0])
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
        provider.config = config
        provider.updated_at = datetime.utcnow().isoformat()

        # Save to JSON file
        self._save()

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
        if self._default_provider_ref[0] == provider_id:
            self._default_provider_ref[0] = None
            # Set new default if there are other providers
            if self._providers:
                self._default_provider_ref[0] = next(iter(self._providers.keys()))

        # Save to JSON file
        self._save()

        return ProviderDeleteResponse(
            success=True, message=f"Provider '{provider_name}' deleted successfully"
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

        self._default_provider_ref[0] = provider_id
        self._save()

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

        self._save()

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
        if self._default_provider_ref[0] == provider_id:
            # Find another enabled provider to be the default
            for pid, p in self._providers.items():
                if pid != provider_id and p.enabled:
                    self._default_provider_ref[0] = pid
                    break
            else:
                self._default_provider_ref[0] = None

        self._save()

        return True

    def get_config(self) -> ProviderConfigResponse:
        """
        Get global configuration.

        Returns:
            ProviderConfigResponse: Global configuration
        """
        return ProviderConfigResponse(
            success=True,
            default_provider=self._default_provider_ref[0],
            version="1.0",
            updated_at=datetime.utcnow().isoformat(),
        )
