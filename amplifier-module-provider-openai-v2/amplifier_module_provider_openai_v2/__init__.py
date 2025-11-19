import json
import logging
import os
from typing import Any

from azure.identity.aio import DefaultAzureCredential
from azure.identity.aio import get_bearer_token_provider
from openai import AsyncOpenAI
from openai.types.responses.easy_input_message_param import EasyInputMessageParam
from openai.types.responses.function_tool_param import FunctionToolParam
from openai.types.responses.response import Response
from openai.types.responses.response_function_tool_call_param import ResponseFunctionToolCallParam
from openai.types.responses.response_input_param import FunctionCallOutput
from openai.types.responses.response_input_param import ResponseInputParam
from openai.types.responses.response_reasoning_item_param import ResponseReasoningItemParam
from openai.types.responses.tool_param import ToolParam
from openai.types.shared.reasoning_effort import ReasoningEffort
from openai.types.shared_params.reasoning import Reasoning
from pydantic import BaseModel
from pydantic import Field

from amplifier_core import ChatRequest
from amplifier_core import ChatResponse
from amplifier_core import ModuleCoordinator
from amplifier_core import ReasoningBlock
from amplifier_core import TextBlock
from amplifier_core import ToolCallBlock
from amplifier_core import ToolResultBlock
from amplifier_core.message_models import ToolCall
from amplifier_core.message_models import ToolSpec
from amplifier_core.message_models import Usage

logger = logging.getLogger(__name__)


class OpenAIV2Config(BaseModel):
    """Configuration for OpenAI v2 provider."""

    model: str = Field(default="gpt-5.1-codex", description="OpenAI model to use")
    reasoning_effort: ReasoningEffort = Field(
        default="medium",
        description='Reasoning effort level: "none", "minimal", "low", "medium", or "high" (options depend on model, see https://platform.openai.com/docs/api-reference/responses/create#responses_create-reasoning)',
    )
    use_azure: bool = Field(
        default=False,
        description="Explicitly use Azure OpenAI. If False, uses OpenAI API. If True, requires AZURE_OPENAI_ENDPOINT environment variable.",
    )


async def mount(coordinator: ModuleCoordinator, config: dict[str, Any] | None = None) -> Any:
    """Mount the OpenAI provider.

    Args:
        coordinator: Module coordinator for managing module lifecycle
        config: Optional configuration dictionary

    Returns:
        Optional cleanup function for unmounting

    Raises:
        ValueError: If API key is not provided (when not using Azure Entra ID)
    """
    config_dict = config or {}

    # Parse and validate config
    provider_config = OpenAIV2Config(**config_dict)

    # Determine if using Azure OpenAI based on explicit config
    if provider_config.use_azure:
        # Check for Azure OpenAI endpoint from environment
        azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")

        if not azure_endpoint:
            raise ValueError("use_azure is True but AZURE_OPENAI_ENDPOINT environment variable is not set.")

        # Normalize Azure endpoint: strip trailing slash and append /openai/v1/
        azure_endpoint = azure_endpoint.rstrip("/")
        base_url = f"{azure_endpoint}/openai/v1/"

        # Check if API key is provided for Azure
        api_key = os.environ.get("AZURE_OPENAI_API_KEY")

        if api_key:
            # Use API key authentication with Azure
            client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            credential = None
        else:
            # Use Entra ID authentication with Azure
            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
            client = AsyncOpenAI(api_key=token_provider, base_url=base_url)
    else:
        # Use standard OpenAI API
        api_key = os.environ.get("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OpenAI provider requires an API key. Set the OPENAI_API_KEY environment variable.")

        client = AsyncOpenAI(api_key=api_key)
        credential = None

    provider = OpenAIProvider(client=client, config=provider_config, coordinator=coordinator)
    await coordinator.mount("providers", provider, name="openai-v2")

    async def cleanup() -> None:
        await client.close()
        if credential:
            await credential.close()

    return cleanup


class OpenAIProvider:
    name = "openai-v2"

    def __init__(
        self,
        client: AsyncOpenAI,
        config: OpenAIV2Config,
        coordinator: ModuleCoordinator | None = None,
    ) -> None:
        self.client = client
        self.config = config
        self.coordinator = coordinator

    async def complete(self, messages: ChatRequest, **kwargs: Any) -> ChatResponse:
        """
        Sends a responses API request to OpenAI and returns the response.

        1. Converts messages: ChatRequest to the Responses API type
        2. Sends the response request
        3. Convert the response to ChatResponse including tool calls
        """
        converted_messages = self._amplifier_to_responses_messages(messages)
        tools = self._amplifier_to_responses_tool_calls(messages.tools or [])
        response = await self.client.responses.create(
            model=self.config.model,
            input=converted_messages,
            tools=tools,
            reasoning={"effort": self.config.reasoning_effort, "summary": "auto"},
            parallel_tool_calls=True,
            max_output_tokens=120_000,
            include=["reasoning.encrypted_content"],
            store=False,
            stream=False,
            truncation="auto",  # Automatically drops items from the beginning of the conversation.
        )
        converted_response = self._responses_to_provider_response(response)
        return converted_response

    def parse_tool_calls(self, response: ChatResponse) -> list[ToolCall]:
        return response.tool_calls or []

    def _amplifier_to_responses_messages(self, messages: ChatRequest) -> ResponseInputParam:
        """Convert Amplifier messages to Responses API messages."""
        response_input_param: ResponseInputParam = []
        for message in messages.messages:
            # Handle string content NOTE there might be better way to handle this case
            if isinstance(message.content, str):
                if message.role in ("system", "user", "assistant"):
                    response_input_param.append(
                        EasyInputMessageParam(
                            type="message",
                            role=message.role,
                            content=message.content,
                        )
                    )
                continue

            # Handle structured content (list of ContentBlocks)
            match message.role:
                case "system":
                    # Each Message with role = "system" with TextBlocks becomes its own EasyInputMessage
                    for content_block in message.content:
                        if isinstance(content_block, TextBlock):
                            response_input_param.append(
                                EasyInputMessageParam(
                                    type="message",
                                    role="system",
                                    content=content_block.text,
                                )
                            )
                case "user":
                    # Each Message with role = "user" with TextBlocks becomes its own EasyInputMessageParam
                    for content_block in message.content:
                        if isinstance(content_block, TextBlock):
                            response_input_param.append(
                                EasyInputMessageParam(
                                    type="message",
                                    role="user",
                                    content=content_block.text,
                                )
                            )
                case "assistant":
                    for content_block in message.content:
                        # Each Message with role = "assistant" with TextBlocks becomes its own EasyInputMessageParam
                        if isinstance(content_block, TextBlock):
                            response_input_param.append(
                                EasyInputMessageParam(
                                    type="message",
                                    role="assistant",
                                    content=content_block.text,
                                )
                            )
                        # Messages with role = Assistant and ToolCall Block are turned into ResponseFunctionToolCallParam
                        elif isinstance(content_block, ToolCallBlock):
                            response_input_param.append(
                                ResponseFunctionToolCallParam(
                                    type="function_call",
                                    name=content_block.name,
                                    call_id=content_block.id,
                                    arguments=json.dumps(content_block.input or {}),
                                )
                            )
                        # Messages with role = Assistant and ReasoningBlock are turned into ResponseReasoningItemParam
                        elif isinstance(content_block, ReasoningBlock):
                            response_input_param.append(self._convert_reasoning_block(content_block))
                # Messages with role = Function and ToolResultBlock are turned into FunctionCallOutput
                case "function":
                    for content_block in message.content:
                        if isinstance(content_block, ToolResultBlock):
                            response_input_param.append(
                                FunctionCallOutput(
                                    type="function_call_output",
                                    call_id=content_block.tool_call_id,
                                    output=content_block.output,
                                )
                            )

        return response_input_param

    def _convert_reasoning_block(self, reasoning_block: ReasoningBlock) -> ResponseReasoningItemParam:
        """Convert Amplifier ReasoningBlock to OpenAI ResponseReasoningItemParam.

        Args:
            reasoning_block: The ReasoningBlock from Amplifier context.
                Content list structure (workaround):
                - content[0] = encrypted_content
                - content[1] = OpenAI reasoning ID (starts with 'rs_')

        Returns:
            ResponseReasoningItemParam suitable for OpenAI Responses API
        """
        # Process summary
        reasoning_summary = []
        if reasoning_block.summary:
            for item in reasoning_block.summary:
                if isinstance(item, str):
                    reasoning_summary.append({"type": "summary_text", "text": item})

        # Extract ID from content[1] (workaround: content[0]=encrypted_content, content[1]=id)
        reasoning_id = reasoning_block.content[1]

        # Build the ResponseReasoningItemParam
        param: ResponseReasoningItemParam = {
            "type": "reasoning",
            "id": reasoning_id,  # Use stored OpenAI reasoning ID
            "summary": reasoning_summary,
        }

        # Add encrypted content if present (content[0])
        if reasoning_block.content and reasoning_block.content[0]:
            param["encrypted_content"] = reasoning_block.content[0]

        return param

    def _amplifier_to_responses_tool_calls(self, tools: list[ToolSpec]) -> list[ToolParam]:
        tool_params: list[ToolParam] = []
        for tool in tools:
            # Currently assume all provided tools will be function tools.
            input_schema = getattr(tool, "input_schema", {"type": "object", "properties": {}, "required": []})
            tool_params.append(
                FunctionToolParam(
                    type="function",
                    name=tool.name,
                    parameters=input_schema,
                    strict=None,
                    description=tool.description or "",
                )
            )
        return tool_params

    def _responses_to_provider_response(self, response: Response) -> ChatResponse:
        """Convert Responses API response to ProviderResponse."""
        content_blocks = []
        tool_calls = []
        for content_block in response.output:
            match content_block.type:
                case "reasoning":
                    content_blocks.append(
                        ReasoningBlock(
                            content=[
                                content_block.encrypted_content
                                or None,  # content[0] = encrypted_content (for reasoning continuity)
                                content_block.id,  # content[1] = id (OpenAI reasoning ID starting with 'rs_')
                            ],
                            summary=[s.text for s in content_block.summary],
                            visibility="internal",  # TODO: Unclear what visibility should be
                        )
                    )
                case "message":
                    text_parts: list[str] = []
                    for part in getattr(content_block, "content", []):
                        if getattr(part, "type", None) == "output_text" and getattr(part, "text", None):
                            text_parts.append(part.text)
                    if text_parts:
                        content_blocks.append(TextBlock(text="".join(text_parts)))
                case "function_call":
                    try:
                        arguments = json.loads(content_block.arguments) if content_block.arguments else {}
                    except json.JSONDecodeError:
                        arguments = {}
                    content_blocks.append(
                        ToolCallBlock(
                            id=content_block.call_id,
                            name=content_block.name,
                            input=arguments,
                            visibility="user",
                        )
                    )
                    tool_calls.append(
                        ToolCall(
                            name=content_block.name,
                            id=content_block.call_id,
                            arguments=arguments,
                        )
                    )

        return ChatResponse(
            content=content_blocks,
            tool_calls=tool_calls,
            usage=self._extract_usage(response),
            degradation=None,
            finish_reason=None,
            metadata=response.to_dict(),
        )

    def _extract_usage(self, response: Response) -> Usage | None:
        usage_stats = getattr(response, "usage", None)
        if usage_stats is None:
            return None

        usage = Usage(
            input_tokens=int(getattr(usage_stats, "input_tokens", 0) or 0),
            output_tokens=int(getattr(usage_stats, "output_tokens", 0) or 0),
            total_tokens=getattr(usage_stats, "total_tokens", 0),
        )
        return usage
