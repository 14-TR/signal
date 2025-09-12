import asyncio
from typing import Any, Dict, List

import requests

# feedparser is an optional dependency that may be missing in some
# environments (e.g. during tests). Import it lazily inside fetch() so
# that the module can be imported without the package installed.
try:  # pragma: no cover - dependency may be missing in tests
    import feedparser
except ModuleNotFoundError:  # pragma: no cover
    feedparser = None  # type: ignore

try:  # pragma: no cover - dependency may be missing in tests
    from modelcontextprotocol import call_tool  # type: ignore
except Exception:  # pragma: no cover
    call_tool = None  # type: ignore

from signalai.models import Item

from . import register
from .base import Source
from .utils import create_item


@register
class RSSSource(Source):
    NAME = "rss"

    def fetch(self, feed_cfg: Dict[str, Any]) -> Any:
        if call_tool:
            async def _fetch() -> Any:
                return await call_tool(
                    "get_feed", {"url": feed_cfg["url"], "num_items": 10}
                )

            return asyncio.run(_fetch())

        response = requests.get(feed_cfg["url"], timeout=10)
        response.raise_for_status()
        if feedparser is None:
            raise RuntimeError(
                "feedparser is required to fetch RSS feeds."
            )
        return feedparser.parse(response.text)

    def parse(self, parsed: Any, feed_cfg: Dict[str, Any]) -> List[Item]:
        if isinstance(parsed, dict):
            entries = parsed.get("items", [])
        else:
            entries = getattr(parsed, "entries", [])
        items: List[Item] = []
        for entry in entries:
            items.append(
                create_item(
                    title=entry.get("title", ""),
                    url=entry.get("link", ""),
                    summary=entry.get("summary", ""),
                    published=entry.get("published"),
                    tags=[],
                    source=feed_cfg["name"],
                )
            )
        return items

