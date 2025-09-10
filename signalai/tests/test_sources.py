import datetime
import types
import pytest

from signalai.sources import rss, arxiv, github
from signalai.models import Item


def _parsed(entries):
    parsed = types.SimpleNamespace()
    parsed.entries = entries
    return parsed


def test_fetch_rss(monkeypatch):
    feed = {"url": "http://example.com/rss", "name": "Example"}
    entry = {
        "title": "T",
        "link": "https://example.com/a",
        "summary": "S",
        "published": "2024-01-01T00:00:00Z",
    }
    monkeypatch.setattr(rss.feedparser, "parse", lambda url: _parsed([entry]))
    items = rss.fetch_rss(feed)
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
    entry = {
        "title": "Paper",
        "link": "https://arxiv.org/abs/1234",
        "summary": "Abstract",
        "published": "2023-12-31T12:00:00Z",
    }
    monkeypatch.setattr(arxiv.feedparser, "parse", lambda url: _parsed([entry]))
    items = arxiv.fetch_arxiv(feed)
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
    feed = {"url": "http://example.com/api", "name": "Repo"}
    release = {
        "name": "v1",
        "html_url": "https://github.com/org/repo/releases/v1",
        "body": "Notes",
        "published_at": "2024-02-02T02:00:00Z",
    }
    class Response:
        def json(self):
            return [release]
        def raise_for_status(self):
            pass
    monkeypatch.setattr(github.requests, "get", lambda url, timeout: Response())
    items = github.fetch_github_releases(feed)
    assert len(items) == 1
    item = items[0]
    assert item.tags == ["release"]
    assert item.source == "Repo"
    assert item.domain == "github.com"
    assert item.title == "v1"
    assert item.url == "https://github.com/org/repo/releases/v1"
    assert item.summary == "Notes"
    assert item.published == datetime.datetime(2024, 2, 2, 2, 0, tzinfo=datetime.timezone.utc)
