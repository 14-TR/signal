import feedparser
from typing import Any, Dict, List

from signalai.models import Item

from . import register
from .base import Source
from .utils import create_item


@register
class ArxivSource(Source):
    NAME = "arxiv"

    def fetch(self, feed_cfg: Dict[str, Any]) -> Any:
        return feedparser.parse(feed_cfg["url"])

    def parse(self, parsed: Any, feed_cfg: Dict[str, Any]) -> List[Item]:
        items: List[Item] = []
        for entry in parsed.entries:
            items.append(
                create_item(
                    title=entry.get("title", ""),
                    url=entry.get("link", ""),
                    summary=entry.get("summary", ""),
                    published=entry.get("published"),
                    tags=["arxiv"],
                    source=feed_cfg["name"],
                )
            )
        return items

