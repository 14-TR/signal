import json
from pathlib import Path
from datetime import datetime, timezone

from signalai.pipeline import ingest, ranker, formatter
from signalai.config import StyleConfig, FormatterConfig
from signalai.models import Item, IssueFinal


def test_ingest_run_adds_new_items(tmp_path, monkeypatch, sample_feed_config):
    feeds_path = tmp_path / "feeds.json"
    store_path = tmp_path / "store.json"
    feeds_path.write_text(json.dumps(sample_feed_config))
    store_path.write_text("[]")

    def dummy_fetcher(feed):
        return [
            Item(
                title="Test",
                url="https://example.com/post?ref=1",
                summary="Summary",
                published=datetime.now(timezone.utc),
                tags=[],
                source="rss",
                domain="example.com",
            )
        ]

    monkeypatch.setitem(ingest.FETCHERS, "rss", dummy_fetcher)

    store_items, new_items = ingest.run(Path(feeds_path), Path(store_path))

    assert len(new_items) == 1
    assert new_items[0].url == "https://example.com/post"
    saved = json.loads(store_path.read_text())
    assert len(saved) == 1


def test_ranker_score_expected(sample_item, expected_score):
    score = ranker.score(sample_item)
    assert abs(score - expected_score) < 1e-6


def test_formatter_beautify_without_llm(sample_draft, expected_markdown):
    cfg = StyleConfig()
    formatter_cfg = FormatterConfig(enable=False)

    result = formatter.beautify(sample_draft, cfg, formatter_cfg, client=None)

    assert isinstance(result, IssueFinal)
    assert expected_markdown in result.markdown
    assert "### Industry" in result.markdown
    assert "- Agent evaluation results [OpenAI]" in result.markdown
    assert "## Predicted Impacts" in result.markdown


def test_formatter_respects_domain_mapping(sample_draft, expected_markdown):
    cfg = StyleConfig(domain_groups={"Research": ["openai.com"]})
    formatter_cfg = FormatterConfig(enable=False)

    result = formatter.beautify(sample_draft, cfg, formatter_cfg, client=None)

    assert expected_markdown in result.markdown
    assert "### Research" in result.markdown
    assert "### Industry" not in result.markdown
