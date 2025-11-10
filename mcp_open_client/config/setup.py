"""
Configuration setup and initialization for MCP Open Client.
"""

import os
import shutil
from pathlib import Path
from typing import Optional

# Default configuration directory
DEFAULT_CONFIG_DIR = Path.home() / ".mcp-open-client"


def get_config_path(filename: str) -> Path:
    """
    Get the full path to a configuration file.

    Args:
        filename: Name of the configuration file

    Returns:
        Path to the configuration file
    """
    return DEFAULT_CONFIG_DIR / filename


def ensure_config_directory() -> Path:
    """
    Ensure the configuration directory exists and initialize default config files.

    This function:
    1. Creates ~/.mcp-open-client/ if it doesn't exist
    2. Creates conversations subdirectory for conversation files
    3. Copies default configuration files ONLY if they don't exist
    4. Preserves existing user configurations

    Returns:
        Path to the configuration directory
    """
    # Create config directory if it doesn't exist
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Create conversations subdirectory
    conversations_dir = DEFAULT_CONFIG_DIR / "conversations"
    conversations_dir.mkdir(exist_ok=True)

    # Get the package's default config files directory
    package_dir = Path(__file__).parent
    defaults_dir = package_dir / "defaults"
    default_configs = {
        "mcp_servers.json": defaults_dir / "mcp_servers.json",
        "ai_providers.json": defaults_dir / "ai_providers.json",
    }

    # Copy default configs only if they don't exist
    for config_name, source_path in default_configs.items():
        dest_path = DEFAULT_CONFIG_DIR / config_name

        # Only copy if destination doesn't exist (preserve user config)
        if not dest_path.exists() and source_path.exists():
            try:
                shutil.copy2(source_path, dest_path)
                print(f"Created default configuration: {dest_path}")
            except Exception as e:
                print(f"Warning: Could not copy {config_name}: {e}")

    return DEFAULT_CONFIG_DIR


def get_config_file(filename: str, create_if_missing: bool = True) -> Optional[Path]:
    """
    Get path to a configuration file, optionally ensuring it exists.

    Args:
        filename: Name of the configuration file
        create_if_missing: If True, initialize config directory if missing

    Returns:
        Path to the configuration file, or None if not found
    """
    if create_if_missing:
        ensure_config_directory()

    config_path = get_config_path(filename)
    return config_path if config_path.exists() else None
