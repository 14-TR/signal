from pydantic import BaseModel
from typing import List

class StyleConfig(BaseModel):
    wrap_col: int = 100
    grouping: List[str] = ["Research", "Industry", "Open Source", "Commentary"]
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

# In a real application, this would be loaded from a TOML file or env vars.
# For now, we'll just use the default settings.
def load_settings() -> Settings:
    return Settings()
