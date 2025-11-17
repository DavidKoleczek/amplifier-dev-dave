import os

import pytest
from openai import AsyncOpenAI

from amplifier_module_provider_openai_v2 import OpenAIProvider


async def test_integration_complete() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set for integration test")

    client = AsyncOpenAI(api_key=api_key)
    provider = OpenAIProvider(client=client, config={})

    try:
        result = await provider.complete([{"role": "user", "content": "Please think hard and say hello!"}])
        print(result)
    finally:
        await client.close()
