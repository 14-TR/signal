import datetime
from typing import List, Optional
import dateutil.parser
from signalai.models import Item
from signalai.io.helpers import domain_of


def parse_published(published: Optional[str]) -> datetime.datetime:
    """Parse a published date string into a timezone-aware datetime.

    If *published* is falsy, the current UTC time is used.
    The function first tries ISO parsing and falls back to generic parsing.
    """
    if not published:
        published = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        return dateutil.parser.isoparse(published)
    except ValueError:
        return dateutil.parser.parse(published)


def create_item(
    title: Optional[str],
    url: Optional[str],
    summary: Optional[str],
    published: Optional[str],
    tags: Optional[List[str]],
    source: str,
) -> Item:
    """Create an :class:`Item` with common sanitisation and defaults."""
    return Item(
        title=title or "",
        url=url or "",
        summary=(summary or "")[:500],
        published=parse_published(published),
        tags=tags or [],
        source=source,
        domain=domain_of(url or ""),
    )
