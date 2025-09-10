from datetime import datetime

from signalai.models import Item
from signalai.config import load_settings, Settings


def make_item(published):
    return Item(
        title="t",
        url="http://e.com",
        summary="s",
        published=published,
        tags=[],
        source="s",
        domain="e.com",
    )


def test_item_parses_published_string():
    item = make_item("2023-01-01T12:30:00Z")
    assert isinstance(item.published, datetime)
    assert item.published.year == 2023
    assert item.published.minute == 30


def test_item_preserves_datetime_instance():
    dt = datetime(2023, 5, 1, 12, 0)
    item = make_item(dt)
    assert item.published is dt


def test_load_settings_provides_defaults():
    settings = load_settings()
    assert isinstance(settings, Settings)
    assert settings.style.wrap_col == 100
    assert settings.formatter.enable is True
