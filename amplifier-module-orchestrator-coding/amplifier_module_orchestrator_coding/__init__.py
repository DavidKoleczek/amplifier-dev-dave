import asyncio
import logging
from typing import Any

from amplifier_core import ContextManager
from amplifier_core import HookRegistry
from amplifier_core import Message
from amplifier_core import ModuleCoordinator
from amplifier_core import Provider
from amplifier_core import TextBlock
from amplifier_core import Tool
from amplifier_core import ToolCallBlock
from amplifier_core import ToolResult
from amplifier_core import ToolResultBlock
from amplifier_core.message_models import ChatRequest
from amplifier_core.message_models import ToolCall
from amplifier_core.message_models import ToolSpec

logger = logging.getLogger(__name__)


async def mount(coordinator: ModuleCoordinator, config: dict[str, Any] | None = None):
    """Mount the coding orchestrator module."""
    config = config or {}

    # Declare observable lifecycle events for this module
    # (hooks-logging will auto-discover and log these)
    coordinator.register_contributor(
        "observability.events",
        "coding-orchestrator",
        lambda: [
            "session:start",  # When session begins
            "session:end",  # When session completes
            "context:pre-compact",  # Before context compaction
        ],
    )

    orchestrator = CodingOrchestrator(config)
    await coordinator.mount("orchestrator", orchestrator)
    logger.info("Mounted CodingOrchestrator with observable events")
    return


class CodingOrchestrator:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.max_iterations = config.get("max_iterations", 100)
        self.max_iterations_message = config.get(
            "max_iterations_message",
            "Max iterations reached. Please generate a final message that discusses the current state we are leaving it in.",
        )

    async def execute(
        self,
        prompt: str,
        context: ContextManager,
        providers: dict[str, Provider],
        tools: dict[str, Tool],
        hooks: HookRegistry,
        coordinator: ModuleCoordinator | None = None,
    ) -> str:
        # Add user prompt to context
        await context.add_message(Message(role="user", content=[TextBlock(text=prompt)]))

        # Get provider and build tool specs once
        provider = self._get_provider(providers)
        tools_specs: list[ToolSpec] = [
            ToolSpec(
                name=name,
                description=tool_obj.description.strip(),
                parameters=tool_obj.input_schema,  # type: ignore
            )
            for name, tool_obj in tools.items()
        ]

        iteration = 0

        # Main orchestration loop - continue until provider stops calling tools
        while True:
            # Check if max iterations reached
            if iteration >= self.max_iterations:
                # Inject user message about max iterations and get final response
                await context.add_message(
                    Message(
                        role="user",
                        content=[TextBlock(text=self.max_iterations_message)],
                    )
                )
                messages = await context.get_messages()
                request = ChatRequest(messages=messages, tools=[])  # No tools for final response
                response = await provider.complete(request)
                # Store ALL blocks from response.content
                await context.add_message(Message(role="assistant", content=response.content))
                return self._extract_text(response.content)

            iteration += 1
            # Get current messages from context and call provider
            messages = await context.get_messages()
            request = ChatRequest(messages=messages, tools=tools_specs)
            response = await provider.complete(request)

            # Store ALL blocks from response.content (including ReasoningBlocks)
            await context.add_message(Message(role="assistant", content=response.content))

            # Check for tool calls by introspecting content blocks
            tool_call_blocks = [block for block in response.content if isinstance(block, ToolCallBlock)]

            if not tool_call_blocks:
                # No tools requested - extract text and return final response
                return self._extract_text(response.content)

            # Tools requested - convert blocks to ToolCall format for execution
            tool_calls = [ToolCall(id=block.id, name=block.name, arguments=block.input) for block in tool_call_blocks]

            # Execute all tools in parallel
            tool_results = await asyncio.gather(*[self._execute_tool(tc, tools, hooks) for tc in tool_calls])

            # Add tool results to context
            for tc, result in zip(tool_calls, tool_results, strict=True):
                output = str(result.output) if result.success else f"Error: {result.error}"
                await context.add_message(
                    Message(role="function", content=[ToolResultBlock(tool_call_id=tc.id, output=output)])
                )

    def _get_provider(self, providers: dict[str, Provider]) -> Provider:
        """
        Get the first provider from the providers dict.
        """
        if not providers:
            raise ValueError("No providers available")
        return next(iter(providers.values()))

    def _extract_text(self, content_blocks: list[Any]) -> str:
        """Extract text from content blocks."""
        text_parts = []
        for block in content_blocks:
            if isinstance(block, TextBlock):
                text_parts.append(block.text)
        return "\n\n".join(text_parts) if text_parts else ""

    async def _execute_tool(self, tool_call: ToolCall, tools: dict[str, Tool], hooks: HookRegistry) -> ToolResult:
        """Execute a single tool call."""
        try:
            # Emit tool:pre hook
            await hooks.emit(
                "tool:pre",
                {
                    "tool_name": tool_call.name,
                    "tool_input": tool_call.arguments,
                    "call_id": tool_call.id,
                },
            )

            tool = tools.get(tool_call.name)
            if not tool:
                error_result = ToolResult(success=False, error={"message": f"Tool '{tool_call.name}' not found"})
                # Emit tool:error hook
                await hooks.emit(
                    "tool:error",
                    {
                        "tool": tool_call.name,
                        "error": f"Tool '{tool_call.name}' not found",
                        "call_id": tool_call.id,
                    },
                )
                return error_result

            result = await tool.execute(tool_call.arguments)

            # Emit tool:post hook
            await hooks.emit(
                "tool:post",
                {
                    "tool_name": tool_call.name,
                    "result": result,
                    "call_id": tool_call.id,
                },
            )

            return result
        except Exception as e:
            logger.error(f"Tool {tool_call.name} failed: {e}")
            error_result = ToolResult(success=False, error={"message": str(e)})
            # Emit tool:error hook
            await hooks.emit(
                "tool:error",
                {
                    "tool": tool_call.name,
                    "error": str(e),
                    "call_id": tool_call.id,
                },
            )
            return error_result
