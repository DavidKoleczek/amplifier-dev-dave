# amplifier-module-provider-openai-v2

OpenAI provider for Amplifier using the Responses API with sensible defaults for coding use.


## Configuration

### Profile Configuration

**OpenAI API (default):**
```yaml
providers:
  - module: provider-openai-v2
    config:
      model: gpt-5.1-codex   # Supports GPT-5 family of models https://platform.openai.com/docs/models
      reasoning_effort: low  # Options depend on the specific model, consult https://platform.openai.com/docs/api-reference/responses/create#responses_create-reasoning
```

**Azure OpenAI:**
```yaml
providers:
  - module: provider-openai-v2
    config:
      use_azure: true        # Explicitly use Azure OpenAI
      model: gpt-5.1-codex   # Your Azure deployment name
      reasoning_effort: high
```

### Environment Variables

Authentication is handled entirely through environment variables to prevent sensitive data from being committed:

**OpenAI API:**
- `OPENAI_API_KEY` - Required for OpenAI API access

**Azure OpenAI with API Key Authentication:**
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint URL (e.g., `https://your-resource.openai.azure.com`)
- `AZURE_OPENAI_API_KEY` - Azure OpenAI API key

**Azure OpenAI with Entra ID Authentication:**
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint URL (e.g., `https://your-resource.openai.azure.com`)
- When `AZURE_OPENAI_API_KEY` is not set, the module automatically uses Microsoft Entra ID (formerly Azure Active Directory) with `DefaultAzureCredential`

**Note:** Set `use_azure: true` in the config to explicitly use Azure OpenAI. This allows you to have both `OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` set and choose which one to use per profile.


## Module Schema

```python
from amplifier_core import ModuleCoordinator, ChatRequest, ChatResponse
from openai import AsyncOpenAI

async def mount(coordinator: ModuleCoordinator, config: dict[str, Any] | None = None) -> Any:
    # Parse config into OpenAIV2Config, create client, instantiate provider
    # Returns cleanup coroutine
    ...

class OpenAIProvider:
    name: str = "openai-v2"

    def __init__(
        self,
        client: AsyncOpenAI,
        config: OpenAIV2Config,
        coordinator: ModuleCoordinator | None = None,
    ) -> None: ...

    async def complete(self, messages: ChatRequest, **kwargs: Any) -> ChatResponse: ...

    def parse_tool_calls(self, response: ChatResponse) -> list[ToolCall]: ...
```

- `mount()` validates config, creates the OpenAI client, and registers the provider
- `complete()` receives `ChatRequest` from orchestrator and returns `ChatResponse`
- `parse_tool_calls()` extracts tool calls from the response for orchestrator to execute


## TODOs

- Fix losing reasoning between steps
- Construct profile with system prompt best for GPT-5.1-codex
- See what happens with built in tools like `web_search`
- Check out `amplifier-core/docs/specs/CONTRIBUTION_CHANNELS.md` to handle context management for stuff specific to provider
