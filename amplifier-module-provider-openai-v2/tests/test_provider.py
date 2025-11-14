"""Tests for OpenAI provider module."""

import pytest

from amplifier_core import ProviderResponse
from amplifier_core import ToolCall
from amplifier_module_provider_openai_v2 import OpenAIProvider


class TestOpenAIProvider:
    """Tests for OpenAIProvider class."""

    @pytest.mark.unit
    async def test_complete(self, openai_config, sample_messages):
        """Test complete() method returns a ProviderResponse."""
        provider = OpenAIProvider(
            api_key=openai_config["api_key"],
            config=openai_config,
        )

        response = await provider.complete(sample_messages)

        print(response)

    @pytest.mark.unit
    def test_parse_tool_calls(self, openai_config):
        """Test parse_tool_calls() method extracts tool calls from response."""
        provider = OpenAIProvider(api_key=openai_config["api_key"], config=openai_config)

        sample_tool_calls = [ToolCall(tool="get_weather", arguments={"location": "San Francisco"}, id="call_123")]
        response = ProviderResponse(content="", tool_calls=sample_tool_calls)
        tool_calls = provider.parse_tool_calls(response)

        print(tool_calls)
