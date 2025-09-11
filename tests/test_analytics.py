import datetime

from signalai import analytics
from signalai.pipeline import ranker
from signalai.models import Item


def make_item():
    return Item(
        title="Test",
        url="http://example.com/a",
        summary="Summary",
        published=datetime.datetime.now(datetime.timezone.utc),
        tags=["security"],
        source="Example",
        domain="example.com",
    )


def test_log_and_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(analytics, "LOG_PATH", tmp_path / "log.csv")
    item = make_item()
    analytics.log_event(item, "view")
    analytics.log_event(item, "click")
    summary = analytics.summarize()
    assert summary["source"]["Example"] == 2
    assert summary["theme"]["security"] == 2


def test_ranking_boost(tmp_path, monkeypatch):
    monkeypatch.setattr(analytics, "LOG_PATH", tmp_path / "log.csv")
    item = make_item()
    base_score = ranker.score(item)
    analytics.log_event(item, "click")
    analytics.log_event(item, "click")
    boosted_score = ranker.score(item)
    assert boosted_score > base_score


def test_personalized_feed(tmp_path, monkeypatch):
    monkeypatch.setattr(analytics, "LOG_PATH", tmp_path / "log.csv")
    item = make_item()
    profile = {"sources": {"Example"}, "themes": set()}
    base_score = ranker.score(item)
    personalized = ranker.score(item, profile)
    assert personalized > base_score
