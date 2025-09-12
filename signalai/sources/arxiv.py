import asyncio
from typing import Any, Dict, List
from urllib.parse import parse_qs, urlparse, quote_plus

import requests
import feedparser

try:  # pragma: no cover
    from modelcontextprotocol import call_tool  # type: ignore
except Exception:  # pragma: no cover
    call_tool = None  # type: ignore

from signalai.models import Item

from . import register
from .base import Source
from .utils import create_item


@register
class ArxivSource(Source):
    NAME = "arxiv"

    def fetch(self, feed_cfg: Dict[str, Any]) -> Any:
        raw_url = feed_cfg.get("url", "")
        parsed_url = urlparse(raw_url)
        query = raw_url
        max_results = 25
        if parsed_url.scheme:
            params = parse_qs(parsed_url.query)
            query = params.get("search_query", [query])[0]
            max_results = int(params.get("max_results", [max_results])[0])

        if call_tool:
            async def _fetch() -> Any:
                return await call_tool(
                    "search_papers",
                    {"query": query, "max_results": max_results},
                )

            return asyncio.run(_fetch())

        api_url = (
            "http://export.arxiv.org/api/query?search_query="
            f"{quote_plus(query)}&max_results={max_results}"
        )
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        return feedparser.parse(response.text)

    def parse(self, parsed: Any, feed_cfg: Dict[str, Any]) -> List[Item]:
        papers: List[Dict[str, Any]] = []
        if isinstance(parsed, dict):
            papers = parsed.get("items") or parsed.get("papers") or []
        else:
            for entry in getattr(parsed, "entries", []):
                papers.append(
                    {
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "summary": entry.get("summary", ""),
                        "published": entry.get("published"),
                    }
                )

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

