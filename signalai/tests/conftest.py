from datetime import datetime, date, timezone

import pytest

from signalai.models import Item, IssueDraft


@pytest.fixture
def sample_item():
    return Item(
        title="Agent evaluation results",
        url="https://openai.com/blog/agents",
        summary="New agent evaluation method",
        published=datetime.now(timezone.utc),
        tags=[],
        source="rss",
        domain="openai.com",
    )


@pytest.fixture
def sample_feed_config():
    return [{"name": "Example", "type": "rss"}]


@pytest.fixture
def sample_draft(sample_item):
    return IssueDraft(
        date=date(2023, 1, 1),
        top_signals=[sample_item],
        bullets=[(sample_item, "New agent evaluation method")],
        impacts_md="Impact text",
        themes={},
    )


@pytest.fixture
def expected_markdown(sample_draft):
    return f"# Signal.ai — {sample_draft.date.isoformat()}"


@pytest.fixture
def expected_score():
    # agent, evaluation, and eval all match boost terms
    keyword_component = 0.75  # 3 hits / 4
    return 0.35 * 1.0 + 0.30 * 1.0 + 0.25 * keyword_component + 0.10 * 0.3
