import asyncio
from typing import Any, Dict, List
from urllib.parse import urlparse

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
class GitHubSource(Source):
    NAME = "github_releases"

    def fetch(self, feed_cfg: Dict[str, Any]) -> Any:
        url = feed_cfg["url"]
        if "://" in url:
            path = urlparse(url).path.strip("/")
        else:
            path = url.strip("/")
        owner, repo, *_ = path.split("/")

        async def _fetch() -> Any:
            return await call_tool(
                "list_releases", {"owner": owner, "repo": repo, "limit": 10}
            )

        return asyncio.run(_fetch())

    def parse(self, releases: Any, feed_cfg: Dict[str, Any]) -> List[Item]:
        rels = releases.get("releases", releases)
        items: List[Item] = []
        for rel in rels[:10]:
            items.append(
                create_item(
                    title=rel.get("name") or rel.get("tag_name", ""),
                    url=rel.get("html_url", ""),
                    summary=rel.get("body"),
                    published=rel.get("published_at"),
                    tags=["release"],
                    source=feed_cfg["name"],
                )
            )
        return items

