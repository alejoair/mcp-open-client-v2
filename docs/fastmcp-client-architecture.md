---
layout: default
title: FastMCP Client Architecture
---

# FastMCP Client Architecture

## Arquitectura Cliente-Transport

FastMCP separa las responsabilidades entre protocolo y conexión:

- **`Client`**: Maneja operaciones del protocolo MCP (tools, resources, prompts)
- **`Transport`**: Establece y mantiene la conexión (WebSockets, HTTP, Stdio, in-memory)

## Ciclo de Vida de Conexión

**CRÍTICO**: Todas las operaciones del cliente requieren usar `async with` para gestión adecuada del ciclo de vida:

```python
async with client:
    # Connection established
    tools = await client.list_tools()
    result = await client.call_tool("tool_name", {"arg": "value"})
# Connection closed automatically
```

## STDIO Transport: Concepto Clave

**El cliente LANZA y GESTIONA el proceso del servidor**:

- El cliente inicia el servidor como subproceso
- Gestiona el ciclo de vida del servidor (start, stop, restart)
- Se comunica a través de stdin/stdout pipes

### Aislamiento de Entorno

Los servidores STDIO corren en entornos AISLADOS por defecto:

- NO heredan variables de entorno del shell
- API keys y configuración deben pasarse explícitamente vía `env`
- El directorio de trabajo puede diferir del shell

```python
from fastmcp.client.transports import StdioTransport

transport = StdioTransport(
    command="python",
    args=["server.py"],
    env={"API_KEY": "secret", "DEBUG": "true"},  # Explícito
    cwd="/path/to/server"
)
```

### keep_alive (Session Persistence)

Por defecto, `keep_alive=True`:
- El subproceso persiste entre conexiones
- Reutiliza el mismo proceso para múltiples operaciones
- Mejora performance

```python
# Default: keep_alive=True
async with client:
    await client.ping()

async with client:  # Reusa el mismo subprocess
    await client.call_tool("tool", {})
```

Para aislamiento completo entre conexiones:

```python
transport = StdioTransport(
    command="python",
    args=["server.py"],
    keep_alive=False  # Nuevo proceso cada vez
)
```

## Diferencia: Client vs async with Client

### Crear vs Conectar

```python
# Crear cliente (NO conecta)
client = Client(transport)

# Conectar y usar (establece conexión)
async with client:
    await client.list_tools()
```

### Problema del Refactor

**ANTES (correcto - lazy init con transports):**
```python
# Crear transport (no inicia proceso)
transport = create_transport(config)
transports[server_id] = transport

# Proceso se inicia on-demand cuando se usa:
async with Client(transport) as client:
    tools = await client.list_tools()
```

**DESPUÉS del refactor (incorrecto - eager init):**
```python
# Crear client (no conecta aún)
client = create_client(config)

# ERROR: Llamar __aenter__() explícitamente bloquea
await client.__aenter__()  # ❌ Se bloquea esperando handshake

# CORRECTO: Dejar que se conecte on-demand
clients[server_id] = client  # Solo guardar

# Conectar cuando se necesite:
async with client:  # ✅ Conecta on-demand
    tools = await client.list_tools()
```

## Solución al Bug

El problema fue agregar `await client.__aenter__()` durante el inicio del servidor, que intenta conectar inmediatamente y se bloquea esperando el handshake MCP.

**Solución: Lazy initialization**
- NO llamar `__aenter__()` al crear el servidor
- Dejar que el client se conecte automáticamente cuando se use con `async with`
- El transport con `keep_alive=True` maneja la persistencia del proceso

```python
# lifecycle_manager.py - CORRECTO
async def start_server(server, clients, process_manager):
    # Crear client sin conectar
    client = create_client(server.config)

    # Solo guardar - NO conectar
    clients[server.id] = client

    # Marcar como running
    server.status = ServerStatus.RUNNING

    return server

# tool_operations.py - CORRECTO
async def get_server_tools(server, client):
    # Conectar on-demand cuando se necesita
    async with client:
        tools = await client.list_tools()
    return tools
```

## Tipos de Transport

1. **STDIO**: Local, cliente gestiona proceso servidor
2. **HTTP/SSE**: Remoto, servidor independiente
3. **In-Memory**: Testing, mismo proceso Python
4. **MCPConfig**: Multi-servidor desde configuración

## Resumen

- Siempre usar `async with client` para operaciones
- STDIO transport: cliente lanza servidor, requiere `env` explícito
- `keep_alive=True`: reutiliza proceso (default)
- NO llamar `__aenter__()` manualmente - lazy initialization
- Conexión on-demand cuando se usa `async with`
