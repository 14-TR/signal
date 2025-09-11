from datetime import datetime, timezone
from unittest.mock import patch

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


def test_cluster_groups_similar_items():
    items = [
        make_item("Agent orchestration breakthrough", "Multi agent coordination"),
        make_item("Orchestrating agents at scale", "Agent swarms"),
        make_item("Benchmark evaluation released", "Evaluation metrics"),
        make_item("Evaluation benchmark improved", "Better benchmarks"),
    ]
    clusters = theme.cluster(items, k_min=2, k_max=2)
    assert len(clusters) == 2
    labels = list(clusters.keys())
    assert any("agent" in lbl.lower() for lbl in labels)
    assert any("evaluation" in lbl.lower() or "benchmark" in lbl.lower() for lbl in labels)


def test_refresh_themes_respects_interval():
    items = [make_item("Agent orchestration", "Coordination")]
    with patch("signalai.pipeline.theme.cluster") as mock_cluster:
        mock_cluster.return_value = {"Agent orchestration": items}
        theme._LAST_CLUSTER = None
        theme.refresh_themes(items, interval_hours=1)
        assert mock_cluster.call_count == 1
        theme.refresh_themes(items, interval_hours=1)
        assert mock_cluster.call_count == 1
        theme.refresh_themes(items, interval_hours=0)
        assert mock_cluster.call_count == 2
