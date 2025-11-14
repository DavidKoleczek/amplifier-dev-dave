"""Tests for OpenAI provider module."""

import os
from types import SimpleNamespace

import pytest

from amplifier_core import ProviderResponse
from amplifier_core import ToolCall
from amplifier_core.content_models import ToolCallContent
from amplifier_module_provider_openai_v2 import OpenAIProvider


@pytest.fixture
def integration_config():
    """Create configuration for integration tests with real API.

    Returns:
        Configuration dictionary with real API key from environment
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set - skipping integration test")

    return {
        "api_key": api_key,
        "default_model": "gpt-5.1-codex",
    }


@pytest.fixture
def sample_messages():
    """Create sample message list for testing.

    Returns:
        List of message dictionaries
    """
    return [
        {"role": "user", "content": "Say hello in exactly 3 words."},
    ]


class TestOpenAIProvider:
    """Tests for OpenAIProvider class."""

    @pytest.mark.integration
    async def test_complete(self, integration_config, sample_messages):
        """Test complete() method makes actual API call and returns a ProviderResponse."""
        provider = OpenAIProvider(
            api_key=integration_config["api_key"],
            config=integration_config,
        )

        response = await provider.complete(sample_messages)

        print(f"\nResponse: {response}")
        print(f"Response content: {response.content}")

    @pytest.mark.unit
    def test_parse_tool_calls_prefers_response_field(self):
        """Existing tool_calls list should be returned unmodified."""
        provider = OpenAIProvider(api_key="sk-fake-key", config={})

        sample_tool_calls = [ToolCall(tool="get_weather", arguments={"location": "San Francisco"}, id="call_123")]
        response = ProviderResponse(content="", tool_calls=sample_tool_calls)
        tool_calls = provider.parse_tool_calls(response)

        assert tool_calls == sample_tool_calls

    @pytest.mark.unit
    def test_parse_tool_calls_from_content_blocks(self):
        """Tool call blocks in content should be converted when list missing."""
        provider = OpenAIProvider(api_key="sk-fake-key", config={})
        block = ToolCallContent(id="call_456", name="lookup_city", arguments={"zip": "94105"})
        response = ProviderResponse(content="", content_blocks=[block])

        tool_calls = provider.parse_tool_calls(response)

        assert len(tool_calls) == 1
        assert tool_calls[0].tool == "lookup_city"
        assert tool_calls[0].arguments == {"zip": "94105"}

    @pytest.mark.unit
    def test_parse_tool_calls_from_raw_response(self):
        """Fallback to raw OpenAI payload when no structured fields exist."""
        provider = OpenAIProvider(api_key="sk-fake-key", config={})
        raw = SimpleNamespace(
            output=[
                {
                    "type": "function_call",
                    "id": "fc_raw",
                    "call_id": "call_raw",
                    "name": "get_weather",
                    "arguments": '{"location": "Berlin"}',
                }
            ]
        )
        response = ProviderResponse(content="", raw=raw)

        tool_calls = provider.parse_tool_calls(response)

        assert len(tool_calls) == 1
        assert tool_calls[0].tool == "get_weather"
        assert tool_calls[0].arguments["location"] == "Berlin"
