from datetime import date, datetime
from typing import List, Optional, Tuple, Dict
import dateutil.parser

from pydantic import BaseModel, field_validator


class Item(BaseModel):
    title: str
    url: str
    summary: str
    published: datetime
    tags: List[str]
    source: str
    hash: Optional[str] = None
    domain: str
    signal: Optional[float] = None

    @field_validator("published", mode="before")
    def parse_published(cls, v):
        if isinstance(v, str):
            return dateutil.parser.parse(v)
        return v


class IssueDraft(BaseModel):
    date: date
    top_signals: List[Item]
    bullets: List[Tuple[Item, str]]
    impacts_md: str
    themes: Dict[str, bool]


class IssueFinal(BaseModel):
    markdown: str
    word_count: int
    links_checked: bool
