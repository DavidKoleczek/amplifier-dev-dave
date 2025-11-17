"""
Provider module for OpenAI (v2).
Integrates with OpenAI API following best practices.
"""

import json
import logging
import os
from typing import Any
from typing import Union

from openai import AsyncOpenAI

from amplifier_core import ModuleCoordinator
from amplifier_core import ProviderResponse
from amplifier_core import ToolCall
from amplifier_core.content_models import ContentBlock
from amplifier_core.content_models import ContentBlockType
from amplifier_core.content_models import TextContent
from amplifier_core.content_models import ThinkingContent
from amplifier_core.content_models import ToolCallContent
from amplifier_core.content_models import ToolResultContent
from amplifier_core.message_models import Message
from amplifier_core.message_models import ReasoningBlock
from amplifier_core.message_models import TextBlock
from amplifier_core.message_models import ThinkingBlock
from amplifier_core.message_models import ToolCallBlock
from amplifier_core.message_models import ToolResultBlock

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

    # Get API key from config or environment
    api_key = config.get("api_key") or os.environ.get("OPENAI_API_KEY")

    if not api_key:
        logger.warning("No OpenAI API key found - provider will not be mounted")
        return None

    # Create provider instance
    provider = OpenAIProvider(api_key=api_key, config=config, coordinator=coordinator)

    # Mount at "providers" mount point
    await coordinator.mount("providers", provider, name="openai-v2")
    logger.info("Mounted OpenAI Provider (v2)")

    # Return cleanup function
    async def cleanup() -> None:
        """Cleanup provider resources."""
        logger.info("Unmounting OpenAI Provider (v2)")
        await provider.client.close()

    return cleanup


class OpenAIProvider:
    """OpenAI provider integration following best practices.

    This provider implements the Amplifier Provider protocol for OpenAI's API.
    It supports chat completions, tool calling, and streaming responses.
    """

    name = "openai-v2"

    def __init__(
        self,
        api_key: str,
        config: dict[str, Any] | None = None,
        coordinator: ModuleCoordinator | None = None,
    ) -> None:
        """Initialize the OpenAI provider.

        Args:
            api_key: OpenAI API key
            config: Optional configuration dictionary
            coordinator: Optional module coordinator for event emission
        """
        self.api_key = api_key
        self.config = config or {}
        self.coordinator = coordinator

        # Configuration with sensible defaults
        self.default_model = self.config.get("default_model", "gpt-5.1-codex")
        self.priority = self.config.get("priority", 100)
        self.base_url = self.config.get("base_url")  # For API proxy support
        self.organization = self.config.get("organization")

        # Responses API specific configuration
        self.default_reasoning_effort = self.config.get("reasoning_effort", "medium")
        self.default_verbosity = self.config.get("verbosity", "medium")
        self.enable_reasoning_traces = self.config.get("enable_reasoning_traces", False)
        self.parallel_tool_calls = self.config.get("parallel_tool_calls", True)

        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            organization=self.organization,
        )

        logger.debug(f"Initialized OpenAI provider with model={self.default_model}")

    async def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> ProviderResponse:
        """Generate completion from messages using OpenAI Responses API.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            **kwargs: Additional parameters:
                - model: Model to use (default: self.default_model)
                - tools: List of tool definitions
                - tool_choice: Tool selection strategy
                - stream: Whether to stream responses (default: False)
                - instructions: System-level guidance/prompt (string)
                - reasoning: Object with 'effort' and 'summary' for reasoning control
                - text: Object with 'verbosity' for output control
                - parallel_tool_calls: Enable concurrent tool invocations (default: True)
                - include: Array of additional data to include (e.g., ["reasoning.encrypted_content"])
                - store: Whether to persist response (default: False)
                - previous_response_id: For conversation continuity

        Returns:
            ProviderResponse with content, usage, and tool calls

        Raises:
            Exception: If API call fails
        """
        # Extract parameters
        model = kwargs.get("model", self.default_model)
        tools = self._convert_tools_to_openai_format(kwargs.get("tools"))
        _tool_choice = kwargs.get("tool_choice")
        _stream = kwargs.get("stream", False)

        # Responses API specific parameters (TODO: Use in implementation)
        _instructions = kwargs.get("instructions")
        _reasoning = kwargs.get("reasoning")
        _text = kwargs.get("text")
        _parallel_tool_calls = kwargs.get("parallel_tool_calls", self.parallel_tool_calls)
        _include = kwargs.get("include")
        _store = kwargs.get("store", False)
        _previous_response_id = kwargs.get("previous_response_id")

        logger.debug(
            f"Generating completion with model={model}, messages={len(messages)}, tools={len(tools) if tools else 0}"
        )

        # Emit request event
        if self.coordinator and hasattr(self.coordinator, "hooks"):
            await self.coordinator.hooks.emit(
                "llm:request",
                {
                    "provider": self.name,
                    "model": model,
                    "message_count": len(messages),
                    "has_tools": bool(tools),
                },
            )

        # Convert messages to OpenAI Responses API format
        input_messages = self._convert_messages_to_openai_format(messages)

        # Build request parameters
        request_params = {"model": model, "input": input_messages}

        # Add tools if provided
        if tools:
            request_params["tools"] = tools

        # Add Responses API specific parameters
        if _instructions:
            request_params["instructions"] = _instructions
        if _reasoning:
            request_params["reasoning"] = _reasoning
        if _text:
            request_params["text"] = _text
        if _parallel_tool_calls is not None:
            request_params["parallel_tool_calls"] = _parallel_tool_calls
        if _include:
            request_params["include"] = _include
        if _store is not None:
            request_params["store"] = _store
        if _previous_response_id:
            request_params["previous_response_id"] = _previous_response_id
        if _stream:
            request_params["stream"] = _stream

        logger.debug(f"Making Responses API call with params: {list(request_params.keys())}")

        # Call OpenAI Responses API
        raw_response = await self.client.responses.create(**request_params)

        logger.debug(f"Received response from OpenAI: {type(raw_response)}")

        response_content, tool_calls, content_blocks, usage = self._parse_openai_response(raw_response)

        # Emit response event
        if self.coordinator and hasattr(self.coordinator, "hooks"):
            await self.coordinator.hooks.emit(
                "llm:response",
                {
                    "provider": self.name,
                    "model": model,
                    "usage": usage,
                    "has_tool_calls": bool(tool_calls),
                    "has_reasoning": any(
                        getattr(block, "type", None) == ContentBlockType.THINKING for block in content_blocks
                    ),
                },
            )

        return ProviderResponse(
            content=response_content,
            raw=raw_response,
            usage=usage,
            tool_calls=tool_calls if tool_calls else None,
            content_blocks=content_blocks if content_blocks else None,
        )

    def parse_tool_calls(self, response: ProviderResponse) -> list[ToolCall]:
        """Derive tool calls from ProviderResponse content.

        Prefers the explicitly populated ``response.tool_calls`` list, but can
        reconstruct calls from content blocks or the raw Responses API payload
        when necessary.
        """

        if response.tool_calls:
            return response.tool_calls

        reconstructed: list[ToolCall] = []

        content_blocks = getattr(response, "content_blocks", None) or []
        for block in content_blocks:
            if isinstance(block, ToolCallContent):
                arguments = block.arguments or {}
                reconstructed.append(ToolCall(tool=block.name, arguments=arguments, id=block.id))
            elif isinstance(block, ToolCallBlock):
                reconstructed.append(ToolCall(tool=block.name, arguments=block.input, id=block.id))

        if reconstructed:
            return reconstructed

        raw_response = getattr(response, "raw", None)
        if raw_response is not None:
            try:
                _, tool_calls, _, _ = self._parse_openai_response(raw_response)
                if tool_calls:
                    return tool_calls
            except Exception as exc:  # pragma: no cover (defensive guard)
                logger.debug("Failed to reparse raw response for tool calls: %s", exc)

        return []

    def _extract_text_from_content(self, content: Union[str, list[Any]]) -> str:
        """Extract text content from string or content blocks.

        Args:
            content: Either a string or list of content blocks

        Returns:
            Extracted text content
        """
        if isinstance(content, str):
            return content

        text_parts = []
        for block in content:
            if isinstance(block, TextBlock):
                text_parts.append(block.text)
            elif isinstance(block, ThinkingBlock):
                # Include thinking as annotation
                text_parts.append(f"[Thinking: {block.thinking}]")

        return " ".join(text_parts) if text_parts else ""

    def _convert_tool_call_block_to_function_call(self, block: ToolCallBlock) -> dict[str, Any]:
        """Convert ToolCallBlock to OpenAI function_call format.

        Args:
            block: Tool call block from Amplifier

        Returns:
            OpenAI function_call item
        """
        return {
            "call_id": block.id,
            "type": "function_call",
            "name": block.name,
            "arguments": json.dumps(block.input),
        }

    def _convert_tool_result_block_to_function_output(self, block: ToolResultBlock) -> dict[str, Any]:
        """Convert ToolResultBlock to OpenAI function_call_output format.

        Args:
            block: Tool result block from Amplifier

        Returns:
            OpenAI function_call_output item
        """
        # Extract output as string
        if isinstance(block.output, str):
            output_str = block.output
        else:
            output_str = json.dumps(block.output)

        return {"type": "function_call_output", "call_id": block.tool_call_id, "output": output_str}

    def _convert_reasoning_block_to_reasoning(self, block: ReasoningBlock) -> dict[str, Any]:
        """Convert ReasoningBlock to OpenAI reasoning format.

        Args:
            block: Reasoning block from Amplifier

        Returns:
            OpenAI reasoning item
        """
        return {
            "type": "reasoning",
            "content": block.content if block.content else [],
            "summary": block.summary if block.summary else [],
        }

    def _convert_assistant_message_content(self, msg: Message) -> list[dict[str, Any]]:
        """Convert assistant message to OpenAI output items.

        Args:
            msg: Assistant message from Amplifier

        Returns:
            List of OpenAI output items (reasoning, function_call, message, etc.)
        """
        output_items = []

        if isinstance(msg.content, str):
            # Simple text message
            if msg.content:
                output_items.append(
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": msg.content, "annotations": []}],
                    }
                )
        else:
            # Content blocks - process each type
            text_blocks = []
            for block in msg.content:
                if isinstance(block, TextBlock):
                    text_blocks.append(block.text)
                elif isinstance(block, ToolCallBlock):
                    output_items.append(self._convert_tool_call_block_to_function_call(block))
                elif isinstance(block, ToolResultBlock):
                    output_items.append(self._convert_tool_result_block_to_function_output(block))
                elif isinstance(block, ReasoningBlock):
                    output_items.append(self._convert_reasoning_block_to_reasoning(block))

            # Add text content as message if any
            if text_blocks:
                combined_text = " ".join(text_blocks)
                output_items.append(
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": combined_text, "annotations": []}],
                    }
                )

        return output_items

    def _convert_function_message(self, msg: Message) -> dict[str, Any]:
        """Convert function result message to OpenAI function_call_output format.

        Args:
            msg: Function message from Amplifier (role='function')

        Returns:
            OpenAI function_call_output item
        """
        # Extract text content
        content_text = self._extract_text_from_content(msg.content)

        return {"type": "function_call_output", "call_id": msg.tool_call_id or "unknown", "output": content_text}

    def _convert_messages_to_openai_format(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert Amplifier messages to OpenAI Responses API format.

        Creates a flat input array mixing role-based messages and output items.
        This matches the OpenAI Responses API structure where previous response
        output items (function_call, reasoning, message) are added directly to
        the input array alongside user/developer messages.

        Args:
            messages: List of Amplifier Message dicts or Message objects

        Returns:
            Flat list for OpenAI 'input' parameter
        """
        input_array = []

        for msg_data in messages:
            # Convert dict to Message object if needed
            if isinstance(msg_data, dict):
                # Handle dict format (role, content, etc.)
                role = msg_data.get("role", "user")
                content = msg_data.get("content", "")
                tool_call_id = msg_data.get("tool_call_id")

                # Simple message conversion
                if role in ["user", "developer", "system"]:
                    input_array.append({"role": role, "content": content if isinstance(content, str) else str(content)})
                elif role == "assistant":
                    # Assistant message - add as message type
                    if content:
                        input_array.append(
                            {
                                "type": "message",
                                "role": "assistant",
                                "content": [
                                    {
                                        "type": "output_text",
                                        "text": content if isinstance(content, str) else str(content),
                                        "annotations": [],
                                    }
                                ],
                            }
                        )
                elif role == "function":
                    # Tool result
                    input_array.append(
                        {
                            "type": "function_call_output",
                            "call_id": tool_call_id or "unknown",
                            "output": content if isinstance(content, str) else str(content),
                        }
                    )
            elif isinstance(msg_data, Message):
                # Handle Message object
                if msg_data.role in ["user", "developer", "system"]:
                    # Simple role-based messages
                    content_text = self._extract_text_from_content(msg_data.content)
                    input_array.append({"role": msg_data.role, "content": content_text})

                elif msg_data.role == "assistant":
                    # Assistant messages - convert to output items
                    output_items = self._convert_assistant_message_content(msg_data)
                    input_array.extend(output_items)

                elif msg_data.role == "function":
                    # Tool result message
                    function_output = self._convert_function_message(msg_data)
                    input_array.append(function_output)

        return input_array

    def _convert_tools_to_openai_format(self, tools: list[Any] | None) -> list[dict[str, Any]] | None:
        """Convert Amplifier tools to OpenAI format.

        Args:
            tools: Amplifier format tools

        Returns:
            OpenAI format tools
        """
        if not tools:
            return None

        converted: list[dict[str, Any]] = []

        for tool in tools:
            if tool is None:
                continue

            # Tool already expressed in OpenAI shape
            if isinstance(tool, dict) and {"type", "name", "parameters"} <= set(tool.keys()):
                converted.append(
                    {
                        "type": tool.get("type", "function"),
                        "name": tool.get("name"),
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters") or {"type": "object", "properties": {}},
                    }
                )
                continue

            # ToolSpec or similar Pydantic model
            dump_fn = getattr(tool, "model_dump", None)
            if callable(dump_fn):
                tool_data = dump_fn()
            elif isinstance(tool, dict):
                tool_data = tool
            else:
                tool_data = {}

            if not isinstance(tool_data, dict):
                tool_data = {}

            name = tool_data.get("name") or getattr(tool, "name", None)
            if not name:
                logger.debug("Skipping tool without name: %s", tool)
                continue

            description = (
                tool_data.get("description") or getattr(tool, "description", None) or getattr(tool, "__doc__", "") or ""
            )

            parameters: Any = tool_data.get("parameters")
            if parameters is None:
                parameters = getattr(tool, "parameters", None)
            if parameters is None:
                parameters = getattr(tool, "input_schema", None)
            if parameters is None:
                parameters = {"type": "object", "properties": {}, "required": []}

            # Ensure parameters is a dict
            param_dump = getattr(parameters, "model_dump", None)
            if callable(param_dump):
                parameters = param_dump()
            if not isinstance(parameters, dict):
                parameters = {"type": "object", "properties": {}, "required": []}

            converted.append({"type": "function", "name": name, "description": description, "parameters": parameters})

        return converted or None

    def _parse_openai_response(self, response: Any) -> tuple[str, list[ToolCall], list[ContentBlock], dict[str, int]]:
        """Parse OpenAI Responses API output into Amplifier types."""

        def _get(value: Any, attr: str, default: Any = None) -> Any:
            if value is None:
                return default
            if isinstance(value, dict):
                return value.get(attr, default)
            return getattr(value, attr, default)

        def _maybe_json(data: Any) -> Any:
            if isinstance(data, str):
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    logger.debug("Failed to decode JSON payload: %s", data)
                    return data
            return data

        def _ensure_dict(value: Any) -> dict[str, Any]:
            if isinstance(value, dict):
                return value
            if value is None:
                return {}
            return {"value": value}

        def _format_reasoning_text(reasoning_item: Any) -> str:
            def _collect_text(entries: Any) -> list[str]:
                texts: list[str] = []
                if isinstance(entries, list):
                    for entry in entries:
                        text = _get(entry, "text")
                        if text:
                            texts.append(text)
                return texts

            summary_texts = _collect_text(_get(reasoning_item, "summary"))
            if summary_texts:
                return "\n".join(summary_texts)

            content_texts = _collect_text(_get(reasoning_item, "content"))
            if content_texts:
                return "\n".join(content_texts)

            fallback = _get(reasoning_item, "text")
            return fallback if isinstance(fallback, str) else ""

        output_items: list[Any] = []
        if response is None:
            output_items = []
        elif hasattr(response, "output"):
            output_items = response.output or []
        elif isinstance(response, dict):
            output_items = response.get("output", []) or []

        content_segments: list[str] = []
        content_blocks: list[ContentBlock] = []
        tool_calls: list[ToolCall] = []

        for item in output_items or []:
            block_type = _get(item, "type")

            if block_type == "message":
                block_content = _get(item, "content", [])
                if isinstance(block_content, list):
                    for content_item in block_content:
                        content_type = _get(content_item, "type")
                        if content_type in {"output_text", "text"}:
                            text = _get(content_item, "text", "")
                            if text:
                                content_segments.append(text)
                                content_blocks.append(TextContent(text=text, raw=content_item))
                        elif content_type in {"output_json", "json_schema"}:
                            json_payload = _get(content_item, "json")
                            if json_payload is not None:
                                text = json.dumps(json_payload)
                                content_segments.append(text)
                                content_blocks.append(TextContent(text=text, raw=content_item))
                        else:
                            text_value = _get(content_item, "text")
                            if text_value:
                                content_segments.append(text_value)
                                content_blocks.append(TextContent(text=text_value, raw=content_item))
                elif isinstance(block_content, str) and block_content:
                    content_segments.append(block_content)
                    content_blocks.append(TextContent(text=block_content))

            elif block_type == "reasoning":
                reasoning_text = _format_reasoning_text(item)
                content_blocks.append(ThinkingContent(text=reasoning_text, raw=item))

            elif block_type in {"thinking", "redacted_thinking"}:
                thinking_text = _get(item, "thinking") or _get(item, "text", "")
                if thinking_text:
                    content_blocks.append(ThinkingContent(text=thinking_text, raw=item))

            elif block_type in {"tool_call", "function_call"}:
                call_id = _get(item, "id") or _get(item, "call_id") or ""
                tool_name = _get(item, "name", "")
                arguments_raw = _get(item, "arguments")
                if arguments_raw is None:
                    arguments_raw = _get(item, "input")

                parsed_arguments = _ensure_dict(_maybe_json(arguments_raw))

                tool_calls.append(ToolCall(tool=tool_name, arguments=parsed_arguments, id=call_id))
                content_blocks.append(ToolCallContent(id=call_id, name=tool_name, arguments=parsed_arguments, raw=item))

            elif block_type == "function_call_output":
                call_id = _get(item, "call_id") or _get(item, "id") or ""
                output_payload = _maybe_json(_get(item, "output"))
                content_blocks.append(ToolResultContent(tool_call_id=call_id, output=output_payload, raw=item))

            elif block_type is None and isinstance(item, str):
                content_segments.append(item)
                content_blocks.append(TextContent(text=item))

        content = "\n\n".join(segment for segment in content_segments if segment)
        usage = self._extract_usage(response)
        return content, tool_calls, content_blocks, usage

    def _extract_usage(self, response: Any) -> dict[str, int]:
        """Extract token usage information from the response."""

        def _safe_int(value: Any) -> int:
            try:
                return int(value) if value is not None else 0
            except (TypeError, ValueError):
                return 0

        usage_obj = None
        if response is None:
            usage_obj = None
        elif hasattr(response, "usage"):
            usage_obj = response.usage
        elif isinstance(response, dict):
            usage_obj = response.get("usage")

        usage: dict[str, int] = {"input": 0, "output": 0, "total": 0}

        if usage_obj is None:
            return usage

        input_tokens = getattr(usage_obj, "input_tokens", None)
        if input_tokens is None and isinstance(usage_obj, dict):
            input_tokens = usage_obj.get("input_tokens")
        if input_tokens is None:
            input_tokens = getattr(usage_obj, "prompt_tokens", None)

        output_tokens = getattr(usage_obj, "output_tokens", None)
        if output_tokens is None and isinstance(usage_obj, dict):
            output_tokens = usage_obj.get("output_tokens")
        if output_tokens is None:
            output_tokens = getattr(usage_obj, "completion_tokens", None)

        total_tokens = getattr(usage_obj, "total_tokens", None)
        if total_tokens is None and isinstance(usage_obj, dict):
            total_tokens = usage_obj.get("total_tokens")

        usage["input"] = _safe_int(input_tokens)
        usage["output"] = _safe_int(output_tokens)
        usage["total"] = _safe_int(total_tokens)

        input_details = getattr(usage_obj, "input_tokens_details", None)
        if input_details is None and isinstance(usage_obj, dict):
            input_details = usage_obj.get("input_tokens_details")
        if input_details:
            cached_tokens = getattr(input_details, "cached_tokens", None)
            if cached_tokens is None and isinstance(input_details, dict):
                cached_tokens = input_details.get("cached_tokens")
            if cached_tokens is not None:
                usage["cached_input_tokens"] = _safe_int(cached_tokens)

        output_details = getattr(usage_obj, "output_tokens_details", None)
        if output_details is None and isinstance(usage_obj, dict):
            output_details = usage_obj.get("output_tokens_details")
        if output_details:
            reasoning_tokens = getattr(output_details, "reasoning_tokens", None)
            if reasoning_tokens is None and isinstance(output_details, dict):
                reasoning_tokens = output_details.get("reasoning_tokens")
            if reasoning_tokens is not None:
                usage["reasoning_output_tokens"] = _safe_int(reasoning_tokens)

        return usage
