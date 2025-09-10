import datetime
from signalai.models import Item
from signalai.rules.authority import AUTHORITY
from signalai.rules.keywords import BOOST_TERMS
from signalai.io.helpers import domain_of

def score(item: Item) -> float:
    """Score = novelty + authority + keyword + engagement(prior)."""
    # Novelty: 1 within 72h, linear decay to 0 by 7 days
    novelty = 0.5
    try:
        age_days = max(0.0, (datetime.datetime.utcnow() - item.published).total_seconds() / 86400.0)
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

    # Keyword match
    text = (item.title + " " + item.summary).lower()
    kw_hits = sum(1 for kw in BOOST_TERMS if kw in text)
    keyword = min(1.0, kw_hits / 4.0)  # saturate quickly

    # Engagement proxy: small prior; bump for GitHub
    engagement = 0.3 + (0.15 if "github.com" in item.domain else 0.0)

    return 0.35 * novelty + 0.30 * authority + 0.25 * keyword + 0.10 * engagement

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
