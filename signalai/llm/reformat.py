from typing import List
import json

from ..models import Item
from .provider import LLMProvider, FallbackProvider
from .cache import LLMCache
from ..config import StyleConfig

def run(
    markdown_draft: str,
    original_items: List[Item],
    provider: LLMProvider,
    cfg: StyleConfig,
    *,
    cache: LLMCache | None = None,
    fallback: LLMProvider | None = None,
) -> str:
    """Uses an LLM to polish the wording and style of a draft newsletter."""

    # Create a locked reference list for the LLM
    refs_list = [{"title": item.title.strip(), "url": item.url} for item in original_items]
    refs_json = json.dumps(refs_list, indent=2)

    system_prompt = f"""You are a precise newsletter formatter. You must:
1.  Keep the same items, titles, and URLs (do not add, remove, or alter them).
2.  Produce clean Markdown only—no HTML.
3.  Use the given section order and grouping.
4.  For each Top Signal: one title line and one single-line summary ({cfg.summary_min_words}–{cfg.summary_max_words} words), neutral and journalistic.
5.  Wrap lines to {cfg.wrap_col} columns; insert a blank line between bullets.
6.  Do not introduce any new links, footnotes, or emojis."""

    user_prompt = f"""# INPUT: LOCKED REFS (DO NOT CHANGE)
```json
{refs_json}
```

# INPUT: DRAFT (CLEANUP & REFORMAT ONLY)
```markdown
{markdown_draft}
```

# TASK
- Reformat the draft into the final house style.
- Where a summary is poor or marked [rewrite required], rewrite it concisely ({cfg.summary_min_words}–{cfg.summary_max_words} words).
- Keep titles and URLs exactly as in LOCKED REFS.
- Group sections as shown; insert '{cfg.section_sep}' before "## Predicted Impacts".
- Output only the final Markdown."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    if fallback:
        provider = FallbackProvider([provider, fallback], cache=cache, retries=2)
    elif cache:
        provider = FallbackProvider([provider], cache=cache, retries=2)

    content = provider.chat(messages)
    return content if content else markdown_draft
