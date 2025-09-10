from typing import List
from ..models import Item
from .client import LLMClient

# No longer needs os or requests
def generate_impacts_llm(items: List[Item], client: LLMClient) -> str:
    """Use an LLM to write the Predicted Impacts section in Markdown bullets."""

    # Compact digest of sources to keep prompt small
    def fmt(it: Item):
        title = (it.title or "").strip()
        src = it.source
        url = it.url
        summ = (it.summary or "").strip().replace("\n", " ")
        if len(summ) > 300:
            summ = summ[:297].rstrip() + "…"
        return f"- Title: {title}\n  Source: {src}\n  URL: {url}\n  Summary: {summ}"

    sources_block = "\n".join(fmt(it) for it in items)

    system_msg = (
        "You are an editor producing a concise, neutral, journalistic Predicted Impacts section "
        "for an AI newsletter. Write 3-5 bullets, 1 sentence each, with concrete who/what/so-what. "
        "Avoid hype and long-term speculation. Output only Markdown bullets."
    )

    user_msg = (
        "Given these Top Signals, write the Predicted Impacts bullets in Markdown. "
        f"Limit to about 180 words total.\n\nTop Signals:\n{sources_block}" # max_words is now part of client
    )

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]

    return client.chat(messages)
