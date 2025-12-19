from unittest.mock import MagicMock, patch

import pytest

from macrolens_poc.config import LLMConfig
from macrolens_poc.llm.openai_provider import OpenAIProvider


@pytest.fixture
def mock_openai_client():
    with patch("macrolens_poc.llm.openai_provider.OpenAI") as mock:
        yield mock


def test_openai_reasoning_params(mock_openai_client):
    """Test that gpt-5 models get the correct reasoning parameters."""
    config = LLMConfig(api_key="test-key", model="openai/gpt-5.2", reasoning_effort="high")
    provider = OpenAIProvider(config)

    # Mock the client instance and create method
    mock_instance = mock_openai_client.return_value
    mock_instance.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="Analysis result"))
    ]

    provider.generate_analysis("System", "User")

    # Verify call arguments
    call_kwargs = mock_instance.chat.completions.create.call_args.kwargs

    assert call_kwargs["model"] == "openai/gpt-5.2"
    assert "extra_body" in call_kwargs
    assert call_kwargs["extra_body"]["reasoning"]["effort"] == "high"


def test_gemini_reasoning_params(mock_openai_client):
    """Test that gemini-3-pro gets the correct reasoning parameters."""
    config = LLMConfig(
        api_key="test-key", model="google/gemini-3-pro-preview", base_url="https://openrouter.ai/api/v1"
    )
    provider = OpenAIProvider(config)

    mock_instance = mock_openai_client.return_value
    mock_instance.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="Analysis result"))
    ]

    provider.generate_analysis("System", "User")

    call_kwargs = mock_instance.chat.completions.create.call_args.kwargs

    assert "extra_body" in call_kwargs
    # Check provider flag (we expect False for OpenRouter leniency)
    assert call_kwargs["extra_body"]["provider"]["require_parameters"] is False
    # Check reasoning params
    assert call_kwargs["extra_body"]["reasoning"]["max_tokens"] == 1000


def test_standard_model_no_reasoning(mock_openai_client):
    """Test that standard models don't get reasoning parameters."""
    config = LLMConfig(api_key="test-key", model="anthropic/claude-4.5-sonnet")
    provider = OpenAIProvider(config)

    mock_instance = mock_openai_client.return_value
    mock_instance.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="Analysis result"))
    ]

    provider.generate_analysis("System", "User")

    call_kwargs = mock_instance.chat.completions.create.call_args.kwargs

    assert "extra_body" not in call_kwargs
    assert "max_tokens" not in call_kwargs  # Unless set in config
