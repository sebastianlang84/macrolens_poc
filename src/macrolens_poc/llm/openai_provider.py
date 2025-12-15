import logging
from typing import Optional

import openai
from openai import OpenAI, APIError, RateLimitError, APIConnectionError

from macrolens_poc.config import LLMConfig
from macrolens_poc.llm.provider import LLMProvider
from macrolens_poc.retry_utils import simple_retry

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    def __init__(self, config: LLMConfig):
        self.config = config
        if not self.config.api_key:
            logger.warning("OpenAI API key not provided. LLM calls will fail.")
        
        logger.info(f"Initializing OpenAIProvider with base_url={self.config.base_url}, model={self.config.model}")
        # OpenRouter requires "Authorization: Bearer <key>" which OpenAI client handles.
        # However, some proxies/gateways might need extra headers.
        # For OpenRouter, it's good practice to send HTTP-Referer and X-Title.
        
        # Ensure we don't pass None as base_url if it's not set, let OpenAI default or handle it.
        # But for OpenRouter we expect it to be set.
        
        kwargs = {
            "api_key": self.config.api_key,
        }
        if self.config.base_url:
            kwargs["base_url"] = self.config.base_url
            
        # Add OpenRouter specific headers if using OpenRouter
        if self.config.base_url and "openrouter" in self.config.base_url:
             kwargs["default_headers"] = {
                "HTTP-Referer": "https://github.com/sebas/macrolens_poc",
                "X-Title": "Macrolens PoC"
            }

        # Explicitly set api_key to avoid "No cookie auth credentials found" if env var is missing/confusing
        # The OpenAI client might be trying to look for other auth methods if api_key is None, but we check that above.
        # However, if api_key is passed as None to OpenAI(), it might trigger the error.
        # We already check self.config.api_key above, but let's be double sure.
        
        if not kwargs.get("api_key"):
             # This should have been caught by the check at the start of __init__, but just in case
             logger.error("API Key is empty in kwargs for OpenAI client!")
             # If we don't have an API key, we can't initialize the client properly for OpenRouter
             # But we might be able to rely on env vars if they are set correctly in the process
             # However, we prefer explicit passing.
        
        # IMPORTANT: If api_key is None, OpenAI client might try to find it in env vars.
        # If it finds nothing, it might default to some other auth method or fail.
        # The "No cookie auth credentials found" error suggests it might be falling back to Azure or some other auth flow?
        # Or maybe it's just a misleading error message when key is missing.
        
        # Force api_key to be a string if it's None, to prevent OpenAI from looking elsewhere
        if kwargs.get("api_key") is None:
             # Try to get from env directly as last resort
             import os
             env_key = os.getenv("OPENAI_API_KEY")
             if env_key:
                 kwargs["api_key"] = env_key
             else:
                 # If still None, we are in trouble. But let's see.
                 pass

        self.client = OpenAI(**kwargs)

    def generate_analysis(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        """
        Generates analysis using OpenAI Chat Completion API with retries.
        """
        if not self.config.api_key:
            raise ValueError("OpenAI API key is missing. Cannot generate analysis.")

        target_model = model or self.config.model

        def _call_openai():
            response = self.client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.temperature,
            )
            return response.choices[0].message.content

        try:
            # Reuse simple_retry logic for robustness
            # We retry on RateLimitError and APIConnectionError specifically
            # APIError is a catch-all, might be risky to retry blindly but okay for PoC
            return simple_retry(
                _call_openai,
                max_attempts=3,
                delay=2.0,
                exceptions=(RateLimitError, APIConnectionError, APIError)
            )
        except Exception as e:
            logger.error(f"Failed to generate analysis from OpenAI: {e}")
            raise