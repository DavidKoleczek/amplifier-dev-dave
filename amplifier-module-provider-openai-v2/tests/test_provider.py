import os

import pytest
from openai import AsyncOpenAI

from amplifier_core import ChatRequest
from amplifier_core import Message
from amplifier_core import ReasoningBlock
from amplifier_core import TextBlock
from amplifier_core import ToolCallBlock
from amplifier_core import ToolResultBlock
from amplifier_module_provider_openai_v2 import OpenAIProvider
from amplifier_module_provider_openai_v2 import OpenAIV2Config


async def test_integration_complete() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set for integration test")

    client = AsyncOpenAI(api_key=api_key)
    config = OpenAIV2Config()
    provider = OpenAIProvider(client=client, config=config)

    try:
        message = Message(role="user", content="Please think hard and say hello!")
        request = ChatRequest(messages=[message])
        result = await provider.complete(request)
        print(result)
    finally:
        await client.close()


async def test_integration_complete_with_content_blocks() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set for integration test")

    client = AsyncOpenAI(api_key=api_key)
    config = OpenAIV2Config()
    provider = OpenAIProvider(client=client, config=config)

    try:
        messages = [
            Message(role="user", content=[TextBlock(text="What is 15 multiplied by 8? Please think hard")]),
            Message(
                role="assistant",
                content=[
                    ReasoningBlock(
                        content=["User is asking for multiplication", "Should use calculator tool for accuracy"],
                        summary=["Need to call calculator with multiply operation"],
                    )
                ],
            ),
            Message(
                role="assistant",
                content=[
                    ToolCallBlock(
                        id="call_multiply_001",
                        name="calculator",
                        input={"operation": "multiply", "a": 15, "b": 8},
                    )
                ],
            ),
            Message(role="function", content=[ToolResultBlock(tool_call_id="call_multiply_001", output="120")]),
            Message(
                role="assistant",
                content=[
                    ReasoningBlock(
                        content=["Received result from calculator", "Formatting response for user"],
                        summary=["The calculation is complete and verified"],
                    )
                ],
            ),
            Message(role="assistant", content=[TextBlock(text="The result of 15 multiplied by 8 is 120.")]),
        ]
        request = ChatRequest(messages=messages)
        result = await provider.complete(request)
        print(result)
    finally:
        await client.close()
