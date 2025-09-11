import requests
from typing import Any, Dict, List

from signalai.models import Item

from . import register
from .base import Source
from .utils import create_item


@register
class GitHubSource(Source):
    NAME = "github_releases"

    def fetch(self, feed_cfg: Dict[str, Any]) -> Any:
        r = requests.get(feed_cfg["url"], timeout=15)
        r.raise_for_status()
        return r.json()

    def parse(self, releases: Any, feed_cfg: Dict[str, Any]) -> List[Item]:
        items: List[Item] = []
        for rel in releases[:10]:
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

