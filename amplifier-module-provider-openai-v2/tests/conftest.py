"""Pytest configuration and fixtures for tests."""

import pytest


@pytest.fixture
def openai_config():
    """Create sample OpenAI configuration for testing.

    Returns:
        Configuration dictionary
    """
    return {
        "api_key": "sk-test-key",
        "default_model": "gpt-4o",
        "max_tokens": 2048,
        "temperature": 0.5,
    }


@pytest.fixture
def sample_messages():
    """Create sample message list for testing.

    Returns:
        List of message dictionaries
    """
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ]
