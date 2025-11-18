import logging
from typing import Any

from amplifier_core import ModuleCoordinator
from amplifier_core.message_models import Message

logger = logging.getLogger(__name__)


async def mount(coordinator: ModuleCoordinator, config: dict[str, Any] | None = None):
    config = config or {}
    context = CodingContextManager()
    await coordinator.mount("context", context)
    logger.info("Mounted CodingContextManager")
    return


class CodingContextManager:
    def __init__(self) -> None:
        self.messages: list[Message] = []

    async def add_message(self, message: Message) -> None:
        """Add a message to the context."""
        # NOTE: Temporary hack for backward compatibility, convert system messages into the Message type
        if isinstance(message, dict) and message.get("role") == "system":
            message = Message(role="system", content=message.get("content", ""))

        self.messages.append(message)
        return

    async def get_messages(self) -> list[Message]:
        """Get all messages in the context."""
        return self.messages.copy()

    async def should_compact(self) -> bool:
        """Check if context should be compacted."""
        return False

    async def compact(self) -> None:
        """Compact the context"""
        return

    async def clear(self) -> None:
        """Clear all messages."""
        self.messages = []
        logger.info("Context cleared")
