import asyncio
from typing import Any, Dict, List

try:  # pragma: no cover - dependency may be missing in tests
    from modelcontextprotocol import call_tool
except Exception:  # pragma: no cover
    async def call_tool(*args, **kwargs):
        raise RuntimeError("modelcontextprotocol is required for MCP calls")

from signalai.models import Item

from . import register
from .base import Source
from .utils import create_item


@register
class RSSSource(Source):
    NAME = "rss"

    def fetch(self, feed_cfg: Dict[str, Any]) -> Any:
        async def _fetch() -> Any:
            return await call_tool(
                "get_feed", {"url": feed_cfg["url"], "num_items": 10}
            )

        return asyncio.run(_fetch())

    def parse(self, parsed: Any, feed_cfg: Dict[str, Any]) -> List[Item]:
        entries = parsed.get("items", []) if isinstance(parsed, dict) else []
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

