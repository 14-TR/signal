import asyncio
from typing import Any, Dict, List

try:  # pragma: no cover
    from modelcontextprotocol import call_tool
except Exception:  # pragma: no cover
    async def call_tool(*args, **kwargs):
        raise RuntimeError("modelcontextprotocol is required for MCP calls")

from signalai.models import Item

from . import register
from .base import Source
from .utils import create_item


@register
class ArxivSource(Source):
    NAME = "arxiv"

    def fetch(self, feed_cfg: Dict[str, Any]) -> Any:
        async def _fetch() -> Any:
            return await call_tool(
                "search_papers",
                {"query": feed_cfg["url"], "max_results": 25},
            )

        return asyncio.run(_fetch())

    def parse(self, parsed: Any, feed_cfg: Dict[str, Any]) -> List[Item]:
        papers = []
        if isinstance(parsed, dict):
            papers = parsed.get("items") or parsed.get("papers") or []

        items: List[Item] = []
        for paper in papers:
            items.append(
                create_item(
                    title=paper.get("title", ""),
                    url=paper.get("link", ""),
                    summary=paper.get("summary") or paper.get("abstract", ""),
                    published=paper.get("published"),
                    tags=["arxiv"],
                    source=feed_cfg["name"],
                )
            )
        return items

