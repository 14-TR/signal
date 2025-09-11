import datetime
import math
import pickle

import pytest

from signalai.models import Item
from signalai.pipeline import ranker


def _make_item() -> Item:
    now = datetime.datetime.now(datetime.timezone.utc)
    return Item(
        title="Agents are here",
        url="https://github.com/example/1",
        summary="Discussion about agents",
        published=now,
        tags=[],
        source="rss",
        domain="github.com",
    )


def test_extract_features():
    item = _make_item()
    feats = ranker.extract_features(item)
    assert feats["novelty"] == pytest.approx(1.0)
    assert feats["authority"] == pytest.approx(0.90)
    assert feats["keyword_hits"] == pytest.approx(2.0)
    assert feats["engagement"] == pytest.approx(0.45)


def test_score_uses_model(tmp_path, monkeypatch):
    item = _make_item()
    weights = [0.1, 0.2, 0.3, 0.4, 0.5]
    model_path = tmp_path / "ranker_model.pkl"
    with model_path.open("wb") as fh:
        pickle.dump(weights, fh)

    monkeypatch.setattr(ranker, "MODEL_PATH", model_path)
    monkeypatch.setattr(ranker, "LOG_PATH", tmp_path / "log.csv")
    monkeypatch.setattr(ranker, "_MODEL_CACHE", None, raising=False)

    score = ranker.score(item)
    feats = ranker.extract_features(item)
    vec = [1.0, feats["novelty"], feats["authority"], feats["keyword_hits"], feats["engagement"]]
    expected = 1.0 / (1.0 + math.exp(-sum(w * x for w, x in zip(weights, vec))))
    assert score == expected
