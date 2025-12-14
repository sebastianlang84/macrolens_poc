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
        
        self.client = OpenAI(api_key=self.config.api_key)

    def generate_analysis(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generates analysis using OpenAI Chat Completion API with retries.
        """
        if not self.config.api_key:
             raise ValueError("OpenAI API key is missing. Cannot generate analysis.")

        def _call_openai():
            response = self.client.chat.completions.create(
                model=self.config.model,
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