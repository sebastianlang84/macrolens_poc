import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from openai import APIConnectionError, APIError, OpenAI, RateLimitError

from macrolens_poc.config import LLMConfig
from macrolens_poc.llm.provider import LLMProvider
from macrolens_poc.retry_utils import simple_retry

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    def __init__(self, config: LLMConfig):
        self.config = config
        api_key = self._resolve_api_key()
        if not api_key:
            logger.error("No API key found for OpenAIProvider (config or env).")
            self.client = None
        else:
            kwargs = self._build_client_kwargs(api_key)
            self.client = OpenAI(**kwargs)
            logger.info(
                f"Initialized OpenAIProvider (base_url={self.config.base_url}, model={self.config.model})"
            )

    def _resolve_api_key(self) -> Optional[str]:
        """Resolves API key from config or environment."""
        if self.config.api_key:
            key = self.config.api_key.get_secret_value()
            if key and key.strip():
                return key.strip()

        import os

        env_key = os.getenv("OPENAI_API_KEY")
        if env_key and env_key.strip():
            return env_key.strip()

        return None

    def _build_client_kwargs(self, api_key: str) -> Dict[str, Any]:
        """Builds arguments for OpenAI client initialization."""
        kwargs = {"api_key": api_key}
        if self.config.base_url:
            kwargs["base_url"] = self.config.base_url

            # OpenRouter specific headers
            parsed = urlparse(self.config.base_url)
            if parsed.netloc.endswith("openrouter.ai"):
                kwargs["default_headers"] = {
                    "HTTP-Referer": "https://github.com/sebas/macrolens_poc",
                    "X-Title": "Macrolens PoC",
                }
        return kwargs

    def _is_transient_error(self, e: Exception) -> bool:
        """Determines if an error is transient and should be retried."""
        if isinstance(e, (APIConnectionError, RateLimitError)):
            return True
        if isinstance(e, APIError):
            # Retry on 5xx, but not on 4xx (except 429 which is RateLimitError)
            status_code = getattr(e, "status_code", None)
            if status_code and 500 <= status_code < 600:
                return True
        return False

    def _build_request_kwargs(
        self, system_prompt: str, user_prompt: str, model: str, include_reasoning: bool = True
    ) -> Dict[str, Any]:
        """Builds arguments for the chat.completions.create call."""
        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.config.temperature,
        }

        if self.config.max_tokens:
            kwargs["max_tokens"] = self.config.max_tokens

        extra_body = {}
        # OpenRouter: be lenient with parameters to avoid 404s on unsupported ones
        if self.config.base_url and "openrouter.ai" in self.config.base_url:
            extra_body["provider"] = {"require_parameters": False}

        if include_reasoning:
            reasoning_param = {}
            # Strategy mapping instead of fragile string contains
            if "gpt-5" in model or "o1" in model or "o3" in model:
                reasoning_param["effort"] = self.config.reasoning_effort or "high"
                # Note: max_tokens here is output tokens. Reasoning budget is internal.
            elif "gemini" in model and "pro" in model:
                # Gemini reasoning budget (internal)
                reasoning_param["max_tokens"] = 1000  # Conservative default

            if reasoning_param:
                extra_body["reasoning"] = reasoning_param

        if extra_body:
            kwargs["extra_body"] = extra_body

        return kwargs

    def generate_analysis(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        """Generates analysis with retries and reasoning fallback."""
        if not self.client:
            raise ValueError("OpenAI client not initialized (missing API key).")

        target_model = model or self.config.model

        def _attempt(include_reasoning: bool):
            kwargs = self._build_request_kwargs(system_prompt, user_prompt, target_model, include_reasoning)
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content

        # Main execution loop with transient retry and reasoning fallback
        last_exception = None
        for attempt_no in range(3):
            try:
                # Try with reasoning first
                return _attempt(include_reasoning=True)
            except Exception as e:
                last_exception = e
                # If it's a 400/404 (likely unsupported reasoning params), retry immediately without reasoning
                status_code = getattr(e, "status_code", None)
                if status_code in (400, 404):
                    logger.warning(f"Reasoning params likely unsupported for {target_model} (HTTP {status_code}). Retrying without reasoning.")
                    try:
                        return _attempt(include_reasoning=False)
                    except Exception as e2:
                        # If even without reasoning it fails, we treat it as a hard error for this attempt
                        last_exception = e2

                if not self._is_transient_error(last_exception):
                    break
                
                import time
                time.sleep(2.0 * (attempt_no + 1))

        logger.error(f"Failed to generate analysis for {target_model}: {last_exception}")
        raise last_exception
