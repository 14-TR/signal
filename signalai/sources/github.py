import requests
from typing import List
from signalai.models import Item
from .utils import create_item

def fetch_github_releases(feed) -> List[Item]:
    r = requests.get(feed["url"], timeout=15)
    r.raise_for_status()
    releases = r.json()
    items: List[Item] = []
    for rel in releases[:10]:
        items.append(
            create_item(
                title=rel.get("name") or rel.get("tag_name", ""),
                url=rel.get("html_url", ""),
                summary=rel.get("body"),
                published=rel.get("published_at"),
                tags=["release"],
                source=feed["name"],
            )
        )
    return items
