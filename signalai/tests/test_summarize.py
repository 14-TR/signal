from datetime import datetime, timezone
from unittest.mock import Mock

from signalai.llm.summarize import summarize_item_llm, top_bullets
from signalai.models import Item


def make_item(summary: str) -> Item:
    return Item(
        title="Title",
        url="https://example.com",
        summary=summary,
        published=datetime.now(timezone.utc),
        tags=[],
        source="rss",
        domain="example.com",
    )


def test_summarize_item_llm_truncates_and_limits_words():
    item = make_item("a" * 700)
    client = Mock()
    client.chat.return_value = " ".join(f"w{i}" for i in range(40))
    result = summarize_item_llm(item, client)
    assert len(result.split()) == 30
    assert result.endswith("…")
    assert client.chat.call_count == 1
    messages = client.chat.call_args[0][0]
    user_content = messages[1]["content"]
    truncated = "a" * 597 + "…"
    assert user_content.endswith(truncated)


def test_top_bullets_use_feed_summary_when_in_range():
    summary = " ".join(f"word{i}" for i in range(15))
    item = make_item(summary)
    client = Mock()
    bullets = top_bullets([item], use_llm=True, client=client)
    assert bullets[0][1] == summary
    client.chat.assert_not_called()


def test_top_bullets_calls_llm_when_summary_out_of_range():
    item = make_item("short")
    client = Mock()
    client.chat.return_value = "llm summary"
    bullets = top_bullets([item], use_llm=True, client=client)
    assert bullets[0][1] == "llm summary"
    client.chat.assert_called_once()


def test_top_bullets_no_llm_when_disabled():
    item = make_item("short")
    client = Mock()
    bullets = top_bullets([item], use_llm=False, client=client)
    assert bullets[0][1] == ""
    client.chat.assert_not_called()
