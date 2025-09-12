import asyncio
from typing import Any, Dict, List
from urllib.parse import parse_qs, urlparse

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
            raw_url = feed_cfg.get("url", "")
            parsed_url = urlparse(raw_url)
            query = raw_url
            max_results = 25
            if parsed_url.scheme:
                params = parse_qs(parsed_url.query)
                query = params.get("search_query", [query])[0]
                max_results = int(params.get("max_results", [max_results])[0])

            return await call_tool(
                "search_papers",
                {"query": query, "max_results": max_results},
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

