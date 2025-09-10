from typing import List, Tuple

from ..models import Item
from ..config import StyleConfig
from .client import LLMClient

def summarize_item_llm(item: Item, client: LLMClient, cfg: StyleConfig) -> str:
    title = (item.title or "").strip()
    src = item.source
    url = item.url
    summ = (item.summary or "").strip().replace("\n", " ")
    if len(summ) > 600:
        summ = summ[:597].rstrip() + "…"

    system_msg = (
        "You are a copy editor. Write a single-line, neutral, journalistic synopsis under "
        f"{cfg.summary_max_words} words. No fluff. Start directly with the finding or action."
    )
    user_msg = f"Title: {title}\nSource: {src}\nURL: {url}\nExisting summary (may be poor): {summ}"

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]
    
    content = client.chat(messages)

    # Post-process to enforce word count, since LLM may ignore it
    content = " ".join(content.split())
    words = content.split()
    if len(words) > cfg.summary_max_words:
        content = " ".join(words[:cfg.summary_max_words]) + "…"
    return content

def top_bullets(
    items: List[Item], use_llm: bool, client: LLMClient, cfg: StyleConfig
) -> List[Tuple[Item, str]]:
    bullets = []
    for it in items:
        feed_sum = (it.summary or "").strip().replace("\n", " ")
        feed_sum = " ".join(feed_sum.split())
        wc = len(feed_sum.split())
        summary_line = ""
        if cfg.summary_min_words <= wc <= cfg.summary_max_words:
            summary_line = feed_sum
        elif use_llm:
            summary_line = summarize_item_llm(it, client, cfg)

        bullets.append((it, summary_line))
    return bullets
