import pytest
from signalai.io.helpers import domain_of, site_label, sha1_of, canonicalize_url


@pytest.mark.parametrize("url,expected", [
    ("https://www.example.com/path", "example.com"),
    ("not a url", ""),
])
def test_domain_of(url, expected):
    assert domain_of(url) == expected


@pytest.mark.parametrize("url,fallback,expected", [
    ("https://arxiv.org/abs/1234", "fallback", "arXiv"),
    ("https://github.com/openai", "fallback", "GitHub"),
    ("https://unknown.com/page", "fallback", "fallback"),
    ("https://unknown.com/page", "", "unknown.com"),
    ("not a url", "", "source"),
])
def test_site_label(url, fallback, expected):
    assert site_label(url, fallback) == expected


def test_sha1_of():
    assert sha1_of("hello") == "aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d"


def test_canonicalize_url():
    assert canonicalize_url(" HTTPS://Example.com/a?b=1 ") == "https://example.com/a"
