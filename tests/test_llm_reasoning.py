from unittest.mock import MagicMock, patch

import pytest

from macrolens_poc.config import LLMConfig
from macrolens_poc.llm.openai_provider import OpenAIProvider


@pytest.fixture
def mock_openai_client():
    with patch("macrolens_poc.llm.openai_provider.OpenAI") as mock:
        yield mock


def test_openai_reasoning_params(mock_openai_client):
    """Test that gpt-5/o1 models get the correct reasoning parameters."""
    config = LLMConfig(api_key="test-key", model="gpt-5.1-preview", reasoning_effort="high")
    provider = OpenAIProvider(config)

    # Mock the client instance and create method
    mock_instance = mock_openai_client.return_value
    mock_instance.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="Analysis result"))
    ]

    provider.generate_analysis("System", "User")

    # Verify call arguments
    call_kwargs = mock_instance.chat.completions.create.call_args.kwargs

    assert call_kwargs["model"] == "gpt-5.1-preview"
    assert "extra_body" in call_kwargs
    assert call_kwargs["extra_body"]["reasoning"]["effort"] == "high"
    # Check default max_tokens for reasoning
    assert call_kwargs["max_tokens"] == 10000


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
    # Check provider flag
    assert call_kwargs["extra_body"]["provider"]["require_parameters"] is True
    # Check reasoning params
    assert call_kwargs["extra_body"]["reasoning"]["max_tokens"] == 8000
    # Check total max_tokens
    assert call_kwargs["max_tokens"] == 12000


def test_standard_model_no_reasoning(mock_openai_client):
    """Test that standard models don't get reasoning parameters."""
    config = LLMConfig(api_key="test-key", model="gpt-4-turbo")
    provider = OpenAIProvider(config)

    mock_instance = mock_openai_client.return_value
    mock_instance.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="Analysis result"))
    ]

    provider.generate_analysis("System", "User")

    call_kwargs = mock_instance.chat.completions.create.call_args.kwargs

    assert "extra_body" not in call_kwargs
    assert "max_tokens" not in call_kwargs  # Unless set in config
