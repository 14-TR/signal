import os
import requests
from typing import Dict, Any, List, Tuple
from ..models import Item
from .client import LLMClient
# TODO: Will need to import domain_of from io.helpers
# TODO: Will need to be updated to use llm.client

def summarize_item_llm(item: Item, client: LLMClient) -> str:
    title = (item.title or "").strip()
    src = item.source
    url = item.url
    summ = (item.summary or "").strip().replace("\n", " ")
    if len(summ) > 600:
        summ = summ[:597].rstrip() + "…"

    system_msg = (
        "You are a copy editor. Write a single-line, neutral, journalistic synopsis under "
        "30 words. No fluff. Start directly with the finding or action."
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
    if len(words) > 30: # max_words is now part of client config, but we can enforce it here
        content = " ".join(words[:30]) + "…"
    return content

def top_bullets(items: List[Item], use_llm: bool, client: LLMClient) -> List[Tuple[Item, str]]:
    bullets = []
    for it in items:
        feed_sum = (it.summary or "").strip().replace("\n", " ")
        feed_sum = " ".join(feed_sum.split())
        wc = len(feed_sum.split())
        summary_line = ""
        if 12 <= wc <= 38: # These numbers should come from StyleConfig
            summary_line = feed_sum
        elif use_llm:
            summary_line = summarize_item_llm(it, client)
        
        bullets.append((it, summary_line))
    return bullets
