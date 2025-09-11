from pathlib import Path
import tomllib
from pydantic import BaseModel
from typing import Dict, List

class StyleConfig(BaseModel):
    wrap_col: int = 100
    grouping: List[str] = ["Research", "Industry", "Open Source", "Commentary"]
    domain_groups: Dict[str, List[str]] = {
        "Research": ["arxiv.org", "research.google", "openreview.net"],
        "Industry": ["openai.com", "anthropic.com", "meta.ai", "google.ai"],
        "Open Source": ["github.com"],
    }
    summary_min_words: int = 12
    summary_max_words: int = 38
    section_sep: str = "---"
    require_summaries: bool = True
    max_top_signals: int = 14
    per_domain_cap: int = 3

class FormatterConfig(BaseModel):
    enable: bool = True
    model: str = "gpt-5-mini"
    temperature: float = 1.0
    max_completion_tokens: int = 1200
    timeout_s: int = 60

class Settings(BaseModel):
    style: StyleConfig = StyleConfig()
    formatter: FormatterConfig = FormatterConfig()


def load_settings(path: Path | None = None) -> Settings:
    """Load settings from a TOML configuration file."""
    if path is None:
        path = Path(__file__).with_name("config.toml")

    with path.open("rb") as f:
        data = tomllib.load(f)

    return Settings.model_validate(data)
