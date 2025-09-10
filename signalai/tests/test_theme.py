from datetime import datetime, timezone
from signalai.pipeline import theme
from signalai.models import Item


def make_item(title: str, summary: str) -> Item:
    return Item(
        title=title,
        url="https://example.com",
        summary=summary,
        published=datetime.now(timezone.utc),
        tags=[],
        source="rss",
        domain="example.com",
    )


def test_detects_expected_themes():
    items = [
        make_item("Agent orchestration breakthrough", "Evaluation benchmark released"),
        make_item("Pruning reduces latency", "Throughput improved"),
        make_item("Vision model", "Multimodal VLM"),
    ]
    themes = theme.detect(items)
    assert themes["Agents & Orchestration"]
    assert themes["Evaluation & QA"]
    assert themes["Model Efficiency (Pruning/Distill/Latency)"]
    assert themes["Multimodal & VLM"]
    assert not themes["Safety & Alignment"]


def test_detects_no_themes_when_keywords_absent():
    items = [make_item("Irrelevant", "Nothing to see here")]
    themes = theme.detect(items)
    assert all(not v for v in themes.values())
