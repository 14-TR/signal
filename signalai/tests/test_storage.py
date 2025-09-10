from datetime import datetime, date
import json
import pytest

from signalai.io.storage import json_serial, load, save


def test_json_serial_handles_supported_types():
    dt = datetime(2023, 1, 1)
    d = date(2023, 1, 2)
    assert json_serial(dt) == "2023-01-01T00:00:00"
    assert json_serial(d) == "2023-01-02"
    with pytest.raises(TypeError):
        json_serial(object())


def test_load_returns_default_when_missing(tmp_path):
    path = tmp_path / "data.json"
    assert load(path, {"a": 1}) == {"a": 1}


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "data.json"
    data = {"time": datetime(2024, 5, 5), "val": 2}
    save(path, data)
    # ensure file contents are serialized correctly
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    assert raw == {"time": "2024-05-05T00:00:00", "val": 2}
    assert load(path, None) == raw


def test_backup_rotation(tmp_path):
    path = tmp_path / "data.json"
    save(path, {"val": 1})
    save(path, {"val": 2})
    bak0 = path.with_suffix(".json.bak0")
    assert bak0.exists()
    with open(bak0, "r", encoding="utf-8") as f:
        assert json.load(f)["val"] == 1

    save(path, {"val": 3})
    bak1 = path.with_suffix(".json.bak1")
    assert bak1.exists()
    with open(bak0, "r", encoding="utf-8") as f:
        assert json.load(f)["val"] == 2
    with open(bak1, "r", encoding="utf-8") as f:
        assert json.load(f)["val"] == 1
