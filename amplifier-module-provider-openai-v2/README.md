# amplifier-module-provider-openai-v2

OpenAI provider for Amplifier using the Responses API with sensible defaults for coding use.


## Module Schema

The provider implements the following interfaces.
Modules are discovered through the `mount` entry point defined in `pyproject.toml`.
The coordinator calls this function once, passing the module configuration, and expects the provider to instantiate itself, register on the `providers` mount point, and return an optional cleanup coroutine.

```python
from amplifier_core import ModuleCoordinator

async def mount(coordinator: ModuleCoordinator, config: dict[str, Any] | None = None) -> Any:
    # Instantiate the provider with config
```

```python
from amplifier_core.models import ProviderResponse
from amplifier_core.models import ToolCall

@runtime_checkable
class Provider(Protocol):
    @property
    def name(self) -> str: ...

    def __init__(self, ..., ) -> None: ...

    async def complete(
        self,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> ProviderResponse: ...

    def parse_tool_calls(self, response: ProviderResponse) -> list[ToolCall]: ...
```

The key requirements are:
- `mount` must resolve credentials/config, instantiate the provider, and register it via `coordinator.mount("providers", provider, name="your-name")`.
- The returned cleanup coroutine should close any persistent resources (HTTP clients, streams, background tasks).
- The provider’s `__init__` captures configuration, establishes any SDK clients, and sets defaults (model, priority, etc.) that the `complete` method will use.
- `complete` is the single entry point the orchestrator calls when it needs a model response;
it receives the plain Python list of message dicts returned by `ContextManager.get_messages()` (see `amplifier-module-loop-streaming/__init__.py:151-185`) plus provider-specific kwargs, and must return a populated `ProviderResponse` that gets surfaced to the user.
- `parse_tool_calls` is invoked immediately afterward so the kernel can translate any native tool/function call artifacts in the provider payload into Amplifier `ToolCall` objects, which are then dispatched to the configured tools before the loop resumes.


## TODOs

- Fix losing reasoning between steps
- Fix empty assistant messages
- Construct profile with system prompt best for GPT-5.1-codex
- See what happens with built in tools like `web_search`
