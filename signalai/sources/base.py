from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from signalai.models import Item


class Source(ABC):
    """Interface for feed sources."""

    NAME: str = ""

    @abstractmethod
    def fetch(self, feed_cfg: Dict[str, Any]) -> Any:
        """Fetch raw data for a feed."""
        raise NotImplementedError

    @abstractmethod
    def parse(self, raw: Any, feed_cfg: Dict[str, Any]) -> List[Item]:
        """Parse raw data into a list of :class:`Item`."""
        raise NotImplementedError

    def dedupe(self, items: List[Item]) -> List[Item]:
        """Optionally deduplicate items."""
        return items
