from datetime import datetime, date
import json
import pytest

from signalai.io.storage import json_serial, load_json, save_json


def test_json_serial_handles_supported_types():
    dt = datetime(2023, 1, 1)
    d = date(2023, 1, 2)
    assert json_serial(dt) == "2023-01-01T00:00:00"
    assert json_serial(d) == "2023-01-02"
    with pytest.raises(TypeError):
        json_serial(object())


def test_load_json_returns_default_when_missing(tmp_path):
    path = tmp_path / "data.json"
    assert load_json(path, {"a": 1}) == {"a": 1}


def test_save_and_load_json_round_trip(tmp_path):
    path = tmp_path / "data.json"
    data = {"time": datetime(2024, 5, 5), "val": 2}
    save_json(path, data)
    # ensure file contents are serialized correctly
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    assert raw == {"time": "2024-05-05T00:00:00", "val": 2}
    assert load_json(path, None) == raw
