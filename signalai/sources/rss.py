import feedparser
from typing import List
from signalai.models import Item
from .utils import create_item

def fetch_rss(feed) -> List[Item]:
    parsed = feedparser.parse(feed["url"])
    items: List[Item] = []
    for entry in parsed.entries:
        items.append(
            create_item(
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                summary=entry.get("summary", ""),
                published=entry.get("published"),
                tags=[],
                source=feed["name"],
            )
        )
    return items
