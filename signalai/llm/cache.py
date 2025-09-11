import hashlib
import json
from typing import Any, Dict, List


class LLMCache:
    """In-memory cache for LLM responses keyed by prompt and model params."""

    def __init__(self):
        self._store: Dict[str, str] = {}

    def _key(self, messages: List[Dict[str, str]], params: Dict[str, Any]) -> str:
        payload = {"messages": messages, "params": params}
        dumped = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(dumped.encode("utf-8")).hexdigest()

    def get(self, messages: List[Dict[str, str]], params: Dict[str, Any]) -> str | None:
        return self._store.get(self._key(messages, params))

    def set(self, messages: List[Dict[str, str]], params: Dict[str, Any], value: str) -> None:
        self._store[self._key(messages, params)] = value
