# UI Architecture

## Overview
Single-page React application using Ant Design components, served as static files by FastAPI at `/ui` endpoint.

## Technology Stack
- **React 18** (CDN) - UI framework
- **Ant Design 5.28** (CDN) - Component library
- **Babel Standalone** - JSX transpilation in browser
- **Tailwind CSS** (CDN) - Utility styles
- **Font Awesome 6.4** (CDN) - Icons
- **Ace Editor 1.32** (CDN) - Code editing

## Directory Structure

```
ui/
├── index.html              # Entry point, imports all dependencies
├── components/             # React components
│   ├── main_layout.js      # Main application layout
│   ├── left_sidebar.js     # Left sidebar with accordion menu
│   ├── right_sidebar.js    # Right sidebar (placeholder)
│   ├── header.js           # Top header bar
│   ├── main_content.js     # Main content area
│   └── configuration.js    # Provider/model configuration form
├── services/               # API communication layer
│   ├── api.js              # Base HTTP client with error handling
│   └── providersService.js # Provider CRUD operations
├── contexts/               # React Context for state management
│   └── ProvidersContext.js # Global provider state
└── hooks/                  # Custom React hooks
    └── useProviders.js     # Hook to access provider context
```

## Architecture Layers

### 1. Service Layer (`services/`)
- **api.js**: Base fetch wrapper with GET/POST/PUT/DELETE methods
- **providersService.js**: All provider-related API calls
  - `getAll()` - List all providers
  - `getById(id)` - Get single provider
  - `setModel(id, type, config)` - Update model configuration

### 2. Context Layer (`contexts/`)
- **ProvidersContext**: Manages global provider state
  - Providers list
  - Default provider ID
  - Loading/error states
  - CRUD operations

### 3. Hooks Layer (`hooks/`)
- **useProviders**: Provides access to ProvidersContext
  - Returns: providers, defaultProvider, loading, error
  - Methods: loadProviders(), getProvider(), updateModelConfig()

### 4. Component Layer (`components/`)
- **MainLayout**: Root layout with sidebars and content area
- **LeftSidebar**: Collapsible sidebar (300px → 80px) with accordion menu
- **RightSidebar**: Collapsible sidebar (placeholder)
- **Header**: Top navigation bar
- **MainContent**: Main content display area
- **Configuration**: Provider/model configuration form
  - Provider selector
  - Main model name and max tokens
  - Small model name and max tokens
  - Save button with validation

## Data Flow

```
Component → useProviders() → ProvidersContext → providersService → api → Backend
```

## Features Implemented

### Configuration Panel
- Auto-loads providers from backend on mount
- Pre-fills form with default provider configuration
- Validates required fields
- Updates main and small model configurations
- Shows success/error messages
- Loading states during API operations

## Styling
- **Sidebars**: Dark gray background (#1f1f1f)
- **Layout**: Full viewport height, responsive collapsing
- **Forms**: Vertical layout with Ant Design validation

## API Endpoint
UI accessible at: `http://127.0.0.1:8001/ui/`
