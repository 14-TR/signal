import pytest
import requests

from signalai.io import http


def _response(status=200, json_data=None):
    resp = requests.Response()
    resp.status_code = status
    resp.url = "https://example.com"
    if json_data is not None:
        import json
        resp._content = json.dumps(json_data).encode("utf-8")
        resp.headers["Content-Type"] = "application/json"
    return resp


def test_request_retries(monkeypatch):
    calls = {"count": 0}

    def fake_request(method, url, timeout=None, **kwargs):
        calls["count"] += 1
        if calls["count"] < 3:
            raise requests.exceptions.Timeout()
        return _response()

    monkeypatch.setattr(requests, "request", fake_request)
    monkeypatch.setattr(http.time, "sleep", lambda *_: None)

    resp = http.request("GET", "https://example.com", retries=3, timeout=1)
    assert calls["count"] == 3
    assert resp.status_code == 200


def test_request_raises(monkeypatch):
    monkeypatch.setattr(requests, "request", lambda *a, **k: _response(status=500))
    with pytest.raises(requests.exceptions.HTTPError):
        http.request("GET", "https://example.com")


def test_get_json(monkeypatch):
    monkeypatch.setattr(requests, "request", lambda *a, **k: _response(json_data={"a": 1}))
    assert http.get_json("https://example.com") == {"a": 1}

