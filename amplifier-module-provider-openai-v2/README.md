# amplifier-module-provider-openai-v2

OpenAI provider module for Amplifier (v2 - best practices edition).

This module provides integration with OpenAI's API, supporting chat completions, tool calling, and streaming responses. It follows Amplifier's provider protocol and best practices for production use.

## Features

- **Chat Completions**: Full support for OpenAI's chat completion API
- **Tool Calling**: Native support for function/tool calling
- **Streaming**: Streaming response support (TODO)
- **Event Emission**: Emits `llm:request` and `llm:response` events for observability
- **Configuration**: Flexible configuration via environment variables or config dictionary
- **Type Safety**: Full type hints and protocol compliance
- **Error Handling**: Robust error handling and logging (TODO)

## Installation

### Development Installation

```bash
cd amplifier-module-provider-openai-v2
uv pip install -e .
```

### Production Installation

```bash
uv pip install amplifier-module-provider-openai-v2
```

## Configuration

The provider can be configured through the Amplifier profile system or environment variables.

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)

### Profile Configuration

```yaml
modules:
  - name: provider-openai-v2
    config:
      api_key: "sk-..."  # Optional, uses OPENAI_API_KEY if not provided
      default_model: "gpt-4o"  # Default: gpt-4o
      max_tokens: 4096  # Default: 4096
      temperature: 0.7  # Default: 0.7
      base_url: null  # Optional: Custom API endpoint
      organization: null  # Optional: OpenAI organization ID
```

## Usage

### Basic Usage

The provider is automatically loaded when included in your Amplifier profile:

```python
# In your Amplifier profile YAML
modules:
  - name: provider-openai-v2
```

### Programmatic Usage

```python
from amplifier_core import ModuleCoordinator
from amplifier_module_provider_openai_v2 import mount

# Initialize coordinator
coordinator = ModuleCoordinator()

# Mount provider
cleanup = await mount(coordinator, config={
    "api_key": "sk-...",
    "default_model": "gpt-4o",
})

# Use provider through coordinator
providers = coordinator.get_mount_point("providers")
openai_provider = providers.get("openai-v2")

# Generate completion
response = await openai_provider.complete(
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.content)
```

## Development

### Prerequisites

- Python 3.11+
- uv package manager

### Setup

```bash
# Install development dependencies
uv pip install -e ".[dev]"
```

### Testing

```bash
# Run all tests
pytest

# Run unit tests only (no API key required)
pytest -m unit

# Run with coverage
pytest --cov=amplifier_module_provider_openai_v2
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Fix linting issues
ruff check --fix .
```

## Architecture

### Provider Protocol

This module implements the Amplifier `Provider` protocol:

- `name: str` - Provider identifier
- `async def complete(messages, **kwargs) -> ProviderResponse` - Generate completions
- `def parse_tool_calls(response) -> list[ToolCall]` - Parse tool calls from response

### Module Lifecycle

1. **Mount**: `mount(coordinator, config)` is called when module loads
2. **Initialization**: Provider instance is created and registered
3. **Usage**: Provider handles completion requests
4. **Cleanup**: Optional cleanup function is called on unmount

### Event System

The provider emits events for observability:

- `llm:request` - Before making API call (includes model, message count)
- `llm:response` - After receiving response (includes usage, tool calls)

## API Reference

### OpenAIProvider

```python
class OpenAIProvider:
    """OpenAI provider integration."""

    name: str = "openai-v2"

    def __init__(
        self,
        api_key: str,
        config: dict[str, Any] | None = None,
        coordinator: ModuleCoordinator | None = None,
    ):
        """Initialize provider."""
        ...

    async def complete(
        self,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> ProviderResponse:
        """Generate completion.

        Args:
            messages: Conversation history
            **kwargs: Additional parameters (model, temperature, tools, etc.)

        Returns:
            ProviderResponse with content and metadata
        """
        ...

    def parse_tool_calls(self, response: ProviderResponse) -> list[ToolCall]:
        """Parse tool calls from response."""
        ...
```

## Roadmap

- [ ] Implement OpenAI API integration
- [ ] Add streaming support
- [ ] Add comprehensive error handling
- [ ] Add retry logic with exponential backoff
- [ ] Add request/response caching
- [ ] Add support for vision (image inputs)
- [ ] Add support for audio (voice inputs)
- [ ] Add comprehensive test coverage
- [ ] Add performance benchmarks
- [ ] Add usage tracking and cost estimation

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Follow the existing code style (use ruff for formatting)
2. Add tests for new features
3. Update documentation as needed
4. Ensure all tests pass before submitting PR

## Support

For issues and questions:

- GitHub Issues: [Create an issue](https://github.com/microsoft/amplifier-dev/issues)
- Documentation: [Amplifier Docs](https://github.com/microsoft/amplifier-dev)
