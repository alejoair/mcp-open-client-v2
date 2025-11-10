# Contributing to MCP Open Client

## Development Setup

### 1. Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### 2. Install Pre-commit Hooks

We use pre-commit hooks to automatically format and lint code before commits.

#### Option A: Using pre-commit framework (Recommended)

```bash
# Install pre-commit (included in dev dependencies)
pip install pre-commit

# Install the git hooks
pre-commit install

# (Optional) Run against all files
pre-commit run --all-files
```

#### Option B: Using git hooks directly

The repository includes a basic pre-commit hook at `.git/hooks/pre-commit` that runs automatically.

## Code Quality Tools

### Formatting

```bash
# Format code with black
black mcp_open_client/

# Sort imports with isort
isort mcp_open_client/
```

### Linting

```bash
# Run flake8
flake8 mcp_open_client/

# Run type checking with mypy
mypy mcp_open_client/
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_open_client

# Run specific test
pytest tests/test_client.py::test_name
```

## Pre-commit Hooks

The pre-commit hooks will automatically:

1. **black**: Format Python code
2. **isort**: Sort imports
3. **flake8**: Lint code (warnings only, won't block commits)
4. **trailing-whitespace**: Remove trailing whitespace
5. **end-of-file-fixer**: Ensure files end with newline
6. **check-yaml**: Validate YAML files
7. **check-json**: Validate JSON files
8. **check-toml**: Validate TOML files
9. **check-merge-conflict**: Check for merge conflict markers

## Commit Message Format

Follow conventional commits format:

```
<type>: <description>

<optional body>

<optional footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Example:
```
feat: Add tool execution endpoint

Add POST /servers/{server_id}/tools/call endpoint to execute
tools on running MCP servers.
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linters
5. Commit your changes (hooks will run automatically)
6. Push to your fork
7. Open a Pull Request

## Code Style Guidelines

- Follow PEP 8 style guide
- Use type hints for all function signatures
- Write docstrings for public functions and classes
- Keep functions focused and single-purpose
- Maximum line length: 88 characters (black default)

## Questions?

Feel free to open an issue for any questions or concerns.
