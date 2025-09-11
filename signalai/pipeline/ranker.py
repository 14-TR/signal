import csv
import datetime
import math
import pickle
from pathlib import Path
from typing import Dict

from signalai.models import Item
from signalai.rules.authority import AUTHORITY
from signalai.rules.keywords import BOOST_TERMS
from signalai import analytics

# Paths for logging and model artifacts
LOG_PATH = Path(__file__).resolve().parents[2] / "out" / "ranker_log.csv"
MODEL_PATH = Path(__file__).resolve().parents[2] / "out" / "ranker_model.pkl"
_MODEL_CACHE: tuple[float, list[float]] | None = None


def extract_features(item: Item) -> Dict[str, float]:
    """Return feature vector used for ranking."""
    # Novelty: 1 within 72h, linear decay to 0 by 7 days
    novelty = 0.5
    try:
        age_days = max(
            0.0,
            (
                datetime.datetime.now(datetime.timezone.utc)
                - item.published
            ).total_seconds()
            / 86400.0,
        )
        if age_days <= 3:
            novelty = 1.0
        elif age_days <= 7:
            novelty = max(0.0, 1.0 - (age_days - 3) / 4.0)
        else:
            novelty = 0.0
    except Exception:
        pass

    # Authority by domain
    authority = AUTHORITY.get(item.domain, 0.6)

    # Keyword hits
    text = (item.title + " " + item.summary).lower()
    kw_hits = sum(1 for kw in BOOST_TERMS if kw in text)

    # Engagement proxy: small prior; bump for GitHub
    engagement = 0.3 + (0.15 if "github.com" in item.domain else 0.0)

    return {
        "novelty": novelty,
        "authority": authority,
        "keyword_hits": float(kw_hits),
        "engagement": engagement,
    }


def _ensure_log_header() -> None:
    if not LOG_PATH.exists():
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("w", newline="") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=[
                    "timestamp",
                    "item_url",
                    "novelty",
                    "authority",
                    "keyword_hits",
                    "engagement",
                    "event",
                ],
            )
            writer.writeheader()


def _log_event(item: Item, features: Dict[str, float], event: str) -> None:
    _ensure_log_header()
    with LOG_PATH.open("a", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "timestamp",
                "item_url",
                "novelty",
                "authority",
                "keyword_hits",
                "engagement",
                "event",
            ],
        )
        writer.writerow(
            {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "item_url": item.url,
                **features,
                "event": event,
            }
        )


def record_interaction(item: Item, event: str) -> None:
    """Log an interaction event such as an open or click."""
    features = extract_features(item)
    _log_event(item, features, event)
    analytics.log_event(item, event)


def _load_model():
    """Load ranking model if available, caching by mtime."""
    global _MODEL_CACHE
    if not MODEL_PATH.exists():
        return None
    mtime = MODEL_PATH.stat().st_mtime
    if _MODEL_CACHE and _MODEL_CACHE[0] == mtime:
        return _MODEL_CACHE[1]
    with MODEL_PATH.open("rb") as fh:
        weights = pickle.load(fh)
    _MODEL_CACHE = (mtime, weights)
    return weights

def score(item: Item, profile: dict[str, set[str]] | None = None) -> float:
    """Score item using trained model if available."""
    features = extract_features(item)
    features["engagement"] += analytics.engagement_boost(item)
    if profile:
        features["engagement"] += analytics.personalized_boost(item, profile)
    _log_event(item, features, "impression")

    model = _load_model()
    if model is not None:
        vec = [
            1.0,
            features["novelty"],
            features["authority"],
            features["keyword_hits"],
            features["engagement"],
        ]
        z = sum(w * x for w, x in zip(model, vec))
        return 1.0 / (1.0 + math.exp(-z))

    # Fallback to heuristic scoring
    keyword = min(1.0, features["keyword_hits"] / 4.0)  # saturate quickly
    return (
        0.35 * features["novelty"]
        + 0.30 * features["authority"]
        + 0.25 * keyword
        + 0.10 * features["engagement"]
    )

def select(items: list[Item], k: int, per_domain_cap: int) -> list[Item]:
    picked, perdom = [], {}
    for it in items:
        if perdom.get(it.domain, 0) >= per_domain_cap:
            continue
        picked.append(it)
        perdom[it.domain] = perdom.get(it.domain, 0) + 1
        if len(picked) >= k:
            break
    return picked
