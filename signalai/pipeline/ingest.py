from pathlib import Path
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from signalai.logging import get_logger

from signalai.io.helpers import canonicalize_url, sha1_of, domain_of
from signalai.io.storage import load, save
from signalai.models import Item
from signalai.sources.arxiv import fetch_arxiv
from signalai.sources.github import fetch_github_releases
from signalai.sources.rss import fetch_rss


logger = get_logger(__name__)

FETCHERS = {
    "rss": fetch_rss,
    "github_releases": fetch_github_releases,
    "arxiv": fetch_arxiv,
}


def _fetch_feed(feed):
    """Helper to fetch a single feed with error handling."""
    ftype = feed.get("type")
    fetcher = FETCHERS.get(ftype)
    if not fetcher:
        logger.warning("Unknown feed type: %s", ftype)
        return []
    try:
        return fetcher(feed)
    except Exception as e:
        logger.error("Fetch error for %s: %s", feed.get("name", ftype), e)
        return []


def run(feeds_path: Path, store_path: Path) -> Tuple[List[Item], List[Item]]:
    """
    Loads feeds, fetches new items, dedupes, and updates the store.
    Returns the full store of items and the list of new items.
    """
    feeds = load(feeds_path, [])
    store_data = load(store_path, [])

    # Backfill domain for old items
    for d in store_data:
        if "domain" not in d and "url" in d:
            d["domain"] = domain_of(d["url"])

    store_items = [Item.parse_obj(d) for d in store_data]
    seen_hashes = {item.hash for item in store_items if item.hash}

    new_items: List[Item] = []
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(_fetch_feed, feed) for feed in feeds]
        for future in as_completed(futures):
            entries = future.result()
            for item in entries:
                url = canonicalize_url(item.url)
                h = sha1_of(url)
                item.hash = h
                item.url = url
                if h not in seen_hashes:
                    new_items.append(item)
                    seen_hashes.add(h)

    store_items.extend(new_items)

    save(store_path, [item.model_dump() for item in store_items])


    return store_items, new_items
