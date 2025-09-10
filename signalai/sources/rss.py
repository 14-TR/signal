import datetime
import feedparser
from typing import List
from signalai.models import Item
from signalai.io.helpers import domain_of
import dateutil.parser

def fetch_rss(feed) -> List[Item]:
    parsed = feedparser.parse(feed["url"])
    items = []
    for entry in parsed.entries:
        published_str = entry.get(
            "published",
            datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        try:
            published_dt = dateutil.parser.isoparse(published_str)
        except ValueError:
            published_dt = dateutil.parser.parse(published_str)


        items.append(Item(
            title=entry.get("title", ""),
            url=entry.get("link", ""),
            summary=entry.get("summary", "")[:500],
            published=published_dt,
            tags=[],
            source=feed["name"],
            domain=domain_of(entry.get("link", "")),
        ))
    return items
