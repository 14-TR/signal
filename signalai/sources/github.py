import datetime
import requests
from typing import List
from signalai.models import Item
from signalai.io.helpers import domain_of
import dateutil.parser

def fetch_github_releases(feed) -> List[Item]:
    r = requests.get(feed["url"], timeout=15)
    r.raise_for_status()
    releases = r.json()
    items = []
    for rel in releases[:10]:
        published_str = rel.get(
            "published_at",
            datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        try:
            published_dt = dateutil.parser.isoparse(published_str)
        except ValueError:
            published_dt = dateutil.parser.parse(published_str)
            
        items.append(Item(
            title=rel.get("name") or rel.get("tag_name", ""),
            url=rel.get("html_url", ""),
            summary=(rel.get("body") or "")[:500],
            published=published_dt,
            tags=["release"],
            source=feed["name"],
            domain=domain_of(rel.get("html_url", "")),
        ))
    return items
