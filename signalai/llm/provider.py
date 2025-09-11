from __future__ import annotations

import os
from typing import List, Dict, Protocol, Optional

import requests

from signalai.logging import get_logger
from .cache import LLMCache

logger = get_logger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM backends."""

    model: str

    def chat(self, messages: List[Dict[str, str]]) -> str:
        ...


class OpenAIProvider:
    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.7,
        max_completion_tokens: int = 256,
        timeout: int = 30,
    ) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model = model or os.getenv("SIGNALAI_LLM_MODEL", "gpt-5-mini")
        self.temperature = temperature
        self.max_completion_tokens = max_completion_tokens
        self.timeout = timeout

    def chat(self, messages: List[Dict[str, str]]) -> str:
        if not self.api_key:
            logger.error("OPENAI_API_KEY not set.")
            return ""

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_completion_tokens": self.max_completion_tokens,
        }

        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            return content
        except requests.exceptions.HTTPError as http_err:
            logger.error("LLM request failed: %s", http_err)
            logger.error("API Response Body: %s", resp.text)
        except Exception as e:
            logger.error("LLM request failed with unexpected error: %s", e)
        return ""


class LocalProvider:
    def __init__(self, model: str = "local") -> None:
        self.model = model

    def chat(self, messages: List[Dict[str, str]]) -> str:
        # Return the last user message as a stubbed "response".
        return messages[-1].get("content", "") if messages else ""


class FallbackProvider:
    """Provider that tries multiple backends with optional caching and retries."""

    def __init__(
        self,
        providers: List[LLMProvider],
        cache: Optional[LLMCache] = None,
        retries: int = 1,
    ) -> None:
        self.providers = providers
        self.cache = cache
        self.retries = retries

    @property
    def model(self) -> str:
        return "+".join(getattr(p, "model", "") for p in self.providers)

    def chat(self, messages: List[Dict[str, str]]) -> str:
        params = {"model": self.model}
        if self.cache:
            cached = self.cache.get(messages, params)
            if cached is not None:
                return cached

        for provider in self.providers:
            for _ in range(self.retries):
                try:
                    resp = provider.chat(messages)
                except Exception:
                    resp = ""
                if resp:
                    if self.cache:
                        self.cache.set(messages, params, resp)
                    return resp
        return ""
