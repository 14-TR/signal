import datetime
import importlib.metadata

from signalai.sources import Source, load_plugins, registry
from signalai.models import Item


def test_fetch_rss(monkeypatch):
    feed = {"url": "http://example.com/rss", "name": "Example"}
    entry = {
        "title": "T",
        "link": "https://example.com/a",
        "summary": "S",
        "published": "2024-01-01T00:00:00Z",
    }

    async def fake_call(tool, params):
        assert tool == "get_feed"
        return {"items": [entry]}

    registry.clear()
    load_plugins(["signalai.sources.rss:RSSSource"])
    src = registry["rss"]()
    monkeypatch.setattr("signalai.sources.rss.call_tool", fake_call)
    parsed = src.fetch(feed)
    items = src.parse(parsed, feed)
    assert len(items) == 1
    item = items[0]
    assert item == Item(
        title="T",
        url="https://example.com/a",
        summary="S",
        published=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        tags=[],
        source="Example",
        domain="example.com",
    )


def test_fetch_arxiv(monkeypatch):
    feed = {"url": "http://example.com/arxiv", "name": "ArxivFeed"}
    paper = {
        "title": "Paper",
        "link": "https://arxiv.org/abs/1234",
        "summary": "Abstract",
        "published": "2023-12-31T12:00:00Z",
    }

    async def fake_call(tool, params):
        assert tool == "search_papers"
        return {"papers": [paper]}

    registry.clear()
    load_plugins(["signalai.sources.arxiv:ArxivSource"])
    src = registry["arxiv"]()
    monkeypatch.setattr("signalai.sources.arxiv.call_tool", fake_call)
    parsed = src.fetch(feed)
    items = src.parse(parsed, feed)
    assert len(items) == 1
    item = items[0]
    assert item.tags == ["arxiv"]
    assert item.source == "ArxivFeed"
    assert item.domain == "arxiv.org"
    assert item.title == "Paper"
    assert item.url == "https://arxiv.org/abs/1234"
    assert item.summary == "Abstract"
    assert item.published == datetime.datetime(2023, 12, 31, 12, 0, tzinfo=datetime.timezone.utc)


def test_fetch_github_releases(monkeypatch):
    feed = {"url": "https://github.com/org/repo", "name": "Repo"}
    release = {
        "name": "v1",
        "html_url": "https://github.com/org/repo/releases/v1",
        "body": "Notes",
        "published_at": "2024-02-02T02:00:00Z",
    }

    async def fake_call(tool, params):
        assert tool == "list_releases"
        return {"releases": [release]}

    registry.clear()
    load_plugins(["signalai.sources.github:GitHubSource"])
    src = registry["github_releases"]()
    monkeypatch.setattr("signalai.sources.github.call_tool", fake_call)
    data = src.fetch(feed)
    items = src.parse(data, feed)
    assert len(items) == 1
    item = items[0]
    assert item.tags == ["release"]
    assert item.source == "Repo"
    assert item.domain == "github.com"
    assert item.title == "v1"
    assert item.url == "https://github.com/org/repo/releases/v1"
    assert item.summary == "Notes"
    assert item.published == datetime.datetime(2024, 2, 2, 2, 0, tzinfo=datetime.timezone.utc)


def test_load_plugins_entry_points(monkeypatch):
    registry.clear()

    class Dummy(Source):
        NAME = "dummy"

        def fetch(self, cfg):
            return None

        def parse(self, raw, cfg):
            return []

    class EP:
        name = "dummy"

        def load(self):
            return Dummy

    monkeypatch.setattr(
        importlib.metadata,
        "entry_points",
        lambda group=None: [EP()] if group == "signalai.sources" else [],
    )
    load_plugins()
    assert "dummy" in registry

