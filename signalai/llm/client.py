import os
import requests
from typing import List, Dict

class LLMClient:
    def __init__(self, model: str, temperature: float, max_completion_tokens: int, timeout: int):
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model = model or os.getenv("SIGNALAI_LLM_MODEL", "gpt-5-mini")
        self.temperature = temperature
        self.max_completion_tokens = max_completion_tokens
        self.timeout = timeout

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Makes a request to a chat completions endpoint.
        Returns the content of the response, or an empty string on failure.
        """
        if not self.api_key:
            print("Error: OPENAI_API_KEY not set.") # Use proper logging
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
            print(f"LLM request failed: {http_err}")
            print(f"API Response Body: {resp.text}") # Added for debugging
            return ""
        except Exception as e:
            print(f"LLM request failed with unexpected error: {e}") # Use proper logging
            return ""
