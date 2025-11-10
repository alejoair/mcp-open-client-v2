# Configuration Management

This module handles configuration file management for MCP Open Client.

## Features

- **Automatic Configuration Directory**: Creates `~/.mcp-open-client/` on first use
- **Default Configuration Files**: Copies default configs if they don't exist
- **Preserves User Settings**: Never overwrites existing configuration files
- **Cross-Platform**: Works on Windows, Linux, and macOS

## Configuration Directory

All configuration files are stored in:
- **Linux/macOS**: `~/.mcp-open-client/`
- **Windows**: `C:\Users\<Username>\.mcp-open-client\`

## Configuration Files

### `mcp_servers.json`
Contains MCP server configurations including:
- Server names and slugs
- Command and arguments
- Environment variables
- Connection status

### `ai_providers.json`
Contains AI provider configurations including:
- Provider names and API endpoints
- API keys (stored securely)
- Model configurations (small and main models)
- Default provider settings

## Usage

### Automatic Initialization

Configuration is automatically initialized when you:
1. Start the API server (`mcp-open-api`)
2. Use the CLI tool (`mcp-open-client`)
3. Import and use the `ProcessManager` or `AIProviderManager`

### Manual Initialization

```python
from mcp_open_client.config import ensure_config_directory, get_config_path

# Ensure config directory exists and initialize default files
config_dir = ensure_config_directory()

# Get path to a specific config file
mcp_servers_path = get_config_path("mcp_servers.json")
ai_providers_path = get_config_path("ai_providers.json")
```

## Installation Behavior

When you install the package with `pip install mcp-open-client`:

1. Default configuration templates are included in the package
2. On first use, these templates are copied to `~/.mcp-open-client/`
3. Existing configuration files are **never** overwritten
4. You can safely upgrade the package without losing your settings

## Resetting Configuration

To reset configuration to defaults, simply delete the config directory:

```bash
# Linux/macOS
rm -rf ~/.mcp-open-client/

# Windows
rmdir /s %USERPROFILE%\.mcp-open-client
```

The next time you use the application, fresh default configs will be created.
