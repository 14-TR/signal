import hashlib
from urllib.parse import urlparse


def domain_of(url: str) -> str:
    try:
        d = urlparse(url).netloc or ""
        return d.replace("www.", "")
    except Exception:
        return ""


def site_label(url: str, fallback: str) -> str:
    d = domain_of(url)
    if "arxiv.org" in d: return "arXiv"
    if "github.com" in d: return "GitHub"
    if "openai.com" in d: return "OpenAI"
    if "deepmind.google" in d: return "DeepMind"
    if "anthropic.com" in d: return "Anthropic"
    if "huggingface.co" in d: return "HF"
    return fallback or (d if d else "source")

def sha1_of(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()

def canonicalize_url(url: str) -> str:
    return url.split("?")[0].strip().lower()
