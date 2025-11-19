"""
Provider management package.

This package provides modular provider management with the following components:
- storage: JSON persistence for provider configurations
- provider_operations: Provider CRUD and state management
- model_operations: Model configuration management
- manager: Main orchestrator class (AIProviderManager)
"""

from .manager import AIProviderManager

__all__ = ["AIProviderManager"]
