"""
Provider storage - JSON persistence for AI provider configurations.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from ...api.models.provider import ProviderConfig, ProviderInfo


class ProviderStorage:
    """Handles JSON persistence for provider configurations."""

    def __init__(self, config_file: Path):
        """
        Initialize provider storage.

        Args:
            config_file: Path to JSON configuration file
        """
        self._config_file = config_file

    def load_providers(
        self,
    ) -> tuple[Dict[str, ProviderInfo], Optional[str]]:
        """
        Load provider configurations from JSON file.

        Returns:
            Tuple of (providers dict, default_provider_id)
        """
        providers: Dict[str, ProviderInfo] = {}
        default_provider: Optional[str] = None

        if not self._config_file.exists():
            return providers, default_provider

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

                    providers[provider_info.id] = provider_info

            # Load default provider
            default_provider = data.get("default_provider")

        except Exception as e:
            # If loading fails, start with empty provider list
            print(
                f"Warning: Failed to load provider configurations from {self._config_file}: {e}"
            )
            providers = {}
            default_provider = None

        return providers, default_provider

    def save_providers(
        self, providers: Dict[str, ProviderInfo], default_provider: Optional[str]
    ) -> None:
        """
        Save provider configurations to JSON file.

        Args:
            providers: Dictionary of provider information
            default_provider: ID of the default provider
        """
        try:
            # Convert providers to dict format
            providers_data = []
            for provider_id, provider in providers.items():
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
                "default_provider": default_provider,
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
