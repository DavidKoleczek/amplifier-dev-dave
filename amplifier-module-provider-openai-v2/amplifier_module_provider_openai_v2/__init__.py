import json
import logging
import os
from typing import Any
from typing import Literal
from typing import cast

from openai import AsyncOpenAI
from openai.types.responses.easy_input_message_param import EasyInputMessageParam
from openai.types.responses.function_tool_param import FunctionToolParam
from openai.types.responses.response import Response
from openai.types.responses.response_function_tool_call_param import ResponseFunctionToolCallParam
from openai.types.responses.response_input_param import FunctionCallOutput
from openai.types.responses.response_input_param import ResponseInputParam
from openai.types.responses.tool_param import ToolParam

from amplifier_core import ModuleCoordinator
from amplifier_core import ProviderResponse
from amplifier_core import ReasoningBlock
from amplifier_core import TextBlock
from amplifier_core import ToolCall
from amplifier_core import ToolCallBlock

logger = logging.getLogger(__name__)


async def mount(coordinator: ModuleCoordinator, config: dict[str, Any] | None = None) -> Any:
    """Mount the OpenAI provider.

    Args:
        coordinator: Module coordinator for managing module lifecycle
        config: Optional configuration dictionary

    Returns:
        Optional cleanup function for unmounting

    Raises:
        ValueError: If API key is not provided
    """
    config = config or {}
    api_key = config.get("api_key") or os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OpenAI provider requires an API key. Set config['api_key'] or the OPENAI_API_KEY environment variable."
        )

    client = AsyncOpenAI(api_key=api_key)
    provider = OpenAIProvider(client=client, config=config, coordinator=coordinator)
    await coordinator.mount("providers", provider, name="openai-v2")

    async def cleanup() -> None:
        await client.close()

    return cleanup


class OpenAIProvider:
    name = "openai-v2"

    def __init__(
        self,
        client: AsyncOpenAI,
        config: dict[str, Any] | None = None,
        coordinator: ModuleCoordinator | None = None,
    ) -> None:
        self.client = client
        self.config = config or {}
        self.coordinator = coordinator

    async def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> ProviderResponse:
        """
        Complete needs to do the following:
        1. Convert messages: list[dict[str, Any]] to the Responses API type
        2. Send the response request
        3. Convert the response to ProviderResponse including tool calls
        """
        converted_messages = self._amplifier_to_responses_messages(messages)
        tools = self._amplifier_to_responses_tool_calls(kwargs.get("tools", []))
        response = await self.client.responses.create(
            model="gpt-5.1-codex",
            input=converted_messages,
            tools=tools,
            reasoning={"effort": "low", "summary": "auto"},
            parallel_tool_calls=True,
            max_output_tokens=120_000,
            include=["reasoning.encrypted_content"],
            store=False,
            stream=False,
            truncation="auto",  # Automatically drops items from the beginning of the conversation.
        )
        converted_response = self._responses_to_provider_response(response)
        return converted_response

    def parse_tool_calls(self, response: ProviderResponse) -> list[ToolCall]:
        return response.tool_calls or []

    def _amplifier_to_responses_messages(self, messages: list[dict[str, Any]]) -> ResponseInputParam:
        """Convert Amplifier messages to Responses API messages."""
        response_input_param: ResponseInputParam = []
        valid_roles: tuple[Literal["user", "assistant", "system", "developer"], ...] = (
            "user",
            "assistant",
            "system",
            "developer",
        )
        for message in messages:
            role = message.get("role")
            content = message.get("content", "")

            if role == "tool":
                call_id = message.get("tool_call_id")
                if not call_id:
                    continue
                output_str = content if isinstance(content, str) else json.dumps(content)
                function_output: FunctionCallOutput = {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": output_str,
                }
                response_input_param.append(function_output)
                continue

            if role not in valid_roles:
                continue
            role_literal = cast(Literal["user", "assistant", "system", "developer"], role)
            easy_message: EasyInputMessageParam = {
                "role": role_literal,
                "content": content,
                "type": "message",
            }
            response_input_param.append(easy_message)

            tool_calls = message.get("tool_calls") or []
            if role == "assistant" and tool_calls:
                for tool_call in tool_calls:
                    call_id = tool_call.get("id") or tool_call.get("call_id")
                    if not call_id:
                        continue
                    arguments = tool_call.get("arguments")
                    arguments_str = arguments if isinstance(arguments, str) else json.dumps(arguments or {})
                    function_call: ResponseFunctionToolCallParam = {
                        "type": "function_call",
                        "name": tool_call.get("tool") or tool_call.get("name") or "",
                        "arguments": arguments_str,
                        "call_id": call_id,
                        "status": "completed",
                    }
                    response_input_param.append(function_call)
        return response_input_param

    def _amplifier_to_responses_tool_calls(self, tools: list) -> list[ToolParam]:
        tool_params: list[ToolParam] = []
        for tool in tools:
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

    def _responses_to_provider_response(self, response: Response) -> ProviderResponse:
        """Convert Responses API response to ProviderResponse."""
        content = response.output_text
        content_blocks = []
        tool_calls = []
        for content_block in response.output:
            match content_block.type:
                case "reasoning":
                    content_blocks.append(
                        ReasoningBlock(
                            content=[
                                content_block.encrypted_content or None
                            ],  # This encrypted content need to be expanded back out for the next request
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
                            tool=content_block.name,
                            id=content_block.call_id,
                            arguments=arguments,
                        )
                    )

        return ProviderResponse(
            content=content,
            raw=response,
            usage=self._extract_usage(response),
            tool_calls=tool_calls,
            content_blocks=content_blocks or None,
        )

    def _extract_usage(self, response: Response) -> dict[str, int] | None:
        usage_stats = getattr(response, "usage", None)
        if usage_stats is None:
            return None

        usage: dict[str, int] = {
            "input": int(getattr(usage_stats, "input_tokens", 0) or 0),
            "output": int(getattr(usage_stats, "output_tokens", 0) or 0),
        }

        total_tokens = getattr(usage_stats, "total_tokens", None)
        if total_tokens is not None:
            usage["total"] = int(total_tokens or 0)

        return usage
