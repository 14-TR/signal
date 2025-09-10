from datetime import datetime, timezone

import pytest

from signalai.models import Item
from signalai.pipeline import ranker
from signalai.config import StyleConfig


@pytest.mark.parametrize("cap,expected", [(1, 2), (2, 4)])
def test_select_respects_per_domain_cap(cap, expected):
    now = datetime.now(timezone.utc)
    items = []
    for i in range(5):
        items.append(
            Item(
                title=f"A{i}",
                url=f"https://a.com/{i}",
                summary="",
                published=now,
                tags=[],
                source="rss",
                domain="a.com",
            )
        )
        items.append(
            Item(
                title=f"B{i}",
                url=f"https://b.com/{i}",
                summary="",
                published=now,
                tags=[],
                source="rss",
                domain="b.com",
            )
        )

    ranked = sorted(items, key=lambda x: x.url)
    cfg = StyleConfig(per_domain_cap=cap)
    selected = ranker.select(ranked, 10, cfg.per_domain_cap)

    assert len(selected) == expected
    assert all(
        sum(1 for it in selected if it.domain == domain) <= cap
        for domain in ["a.com", "b.com"]
    )

