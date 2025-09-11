import csv
import datetime
from collections import defaultdict
from pathlib import Path
from typing import Dict, Set

from .models import Item

# Path for engagement events log
LOG_PATH = Path(__file__).resolve().parent.parent / "out" / "engagement_log.csv"


def _ensure_header() -> None:
    if LOG_PATH.exists():
        return
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["timestamp", "item_url", "source", "themes", "event"],
        )
        writer.writeheader()


def log_event(item: Item, event: str) -> None:
    """Log a user engagement event for an item."""
    _ensure_header()
    with LOG_PATH.open("a", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["timestamp", "item_url", "source", "themes", "event"],
        )
        writer.writerow(
            {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "item_url": item.url,
                "source": item.source,
                "themes": "|".join(item.tags),
                "event": event,
            }
        )


def summarize() -> Dict[str, Dict[str, int]]:
    """Aggregate engagement counts by source and theme."""
    by_source: Dict[str, int] = defaultdict(int)
    by_theme: Dict[str, int] = defaultdict(int)
    if not LOG_PATH.exists():
        return {"source": {}, "theme": {}}
    with LOG_PATH.open() as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            by_source[row["source"]] += 1
            themes = row["themes"].split("|") if row["themes"] else []
            for t in themes:
                by_theme[t] += 1
    return {"source": dict(by_source), "theme": dict(by_theme)}


def engagement_boost(item: Item) -> float:
    """Return a normalized engagement boost for the given item."""
    summary = summarize()
    source_counts = summary["source"]
    theme_counts = summary["theme"]
    source_max = max(source_counts.values(), default=0)
    theme_max = max(theme_counts.values(), default=0)
    src_score = (
        source_counts.get(item.source, 0) / source_max if source_max else 0.0
    )
    theme_score = 0.0
    if item.tags and theme_max:
        theme_score = max(theme_counts.get(t, 0) for t in item.tags) / theme_max
    return 0.2 * max(src_score, theme_score)


def personalized_boost(item: Item, profile: Dict[str, Set[str]]) -> float:
    """Return boost based on user profile preferences."""
    boost = 0.0
    if item.source in profile.get("sources", set()):
        boost += 0.2
    if any(tag in profile.get("themes", set()) for tag in item.tags):
        boost += 0.2
    return boost
