import textwrap
from typing import Dict, List, Tuple
from collections import defaultdict
import html
import re

from signalai.logging import get_logger

from ..models import IssueDraft, IssueFinal, Item
from ..config import StyleConfig, FormatterConfig
from ..llm.client import LLMClient
from ..llm import reformat as llm_reformat
from . import validators
from ..io.helpers import site_label


logger = get_logger(__name__)


def _group_items(
    items: List[Item], domain_groups: Dict[str, List[str]], default_group: str = "Commentary"
) -> Dict[str, List[Item]]:
    """Groups items into categories based on domain rules."""
    groups = defaultdict(list)
    for item in items:
        domain = item.domain
        matched = False
        for group_name, domains in domain_groups.items():
            if any(d in domain for d in domains):
                groups[group_name].append(item)
                matched = True
                break
        if not matched:
            groups[default_group].append(item)
    return groups

def _pre_lint(draft: IssueDraft, cfg: StyleConfig) -> Tuple[str, List[Dict[str,str]]]:
    """Cleans, groups, and assembles a pre-formatted markdown string and a reference list."""
    lines = []
    lines.append(f"# Signal.ai — {draft.date.isoformat()}\n")
    lines.append("## Top Signals")

    grouped_items = _group_items(draft.top_signals, cfg.domain_groups)
    summary_map = {bullet[0].hash: bullet[1] for bullet in draft.bullets}

    for group_name in cfg.grouping:
        if group_name in grouped_items:
            lines.append(f"\n### {group_name}")
            for item in grouped_items[group_name]:
                title = html.unescape(" ".join(item.title.split()))
                site = site_label(item.url, item.source)
                
                # Dynamically clamp title based on the full line length
                suffix = f" [{site}]({item.url})"
                available_len = cfg.wrap_col - len(suffix) - 3 # -3 for "- " and "…"
                clamped_title = title[:available_len] + "…" if len(title) > available_len else title

                lines.append(f"- {clamped_title}{suffix}")

                summary = summary_map.get(item.hash, "")
                # Clean and strip HTML tags
                summary = re.sub('<[^<]+?>', '', summary)
                summary = html.unescape(" ".join(summary.split()))
                word_count = len(summary.split())

                if cfg.summary_min_words <= word_count <= cfg.summary_max_words:
                    # Apply indentation directly within textwrap for accurate wrapping
                    wrapped = textwrap.fill(
                        summary,
                        width=cfg.wrap_col,
                        initial_indent="  ",
                        subsequent_indent="  "
                    )
                    lines.append(wrapped)
                else:
                    lines.append(f"  [rewrite required]")
    
    lines.append(f"\n{cfg.section_sep}\n")
    lines.append("## Predicted Impacts")
    lines.append(draft.impacts_md)

    refs = [{"title": item.title, "url": item.url} for item in draft.top_signals]
    return "\n".join(lines), refs


def beautify(
    draft: IssueDraft,
    cfg: StyleConfig,
    formatter_cfg: FormatterConfig,
    client: LLMClient
) -> IssueFinal:
    """The main orchestration function for formatting the newsletter."""
    
    pre_linted_md, refs = _pre_lint(draft, cfg)

    if formatter_cfg.enable:
        polished_markdown = llm_reformat.run(
            markdown_draft=pre_linted_md,
            original_items=draft.top_signals,
            client=client,
            cfg=cfg,
        )
        
        is_valid, errors = validators.validate(polished_markdown, draft.top_signals, cfg)

        if is_valid:
            final_markdown = polished_markdown
        else:
            logger.warning("LLM output validation failed. Falling back to pre-linted version.")
            for err in errors:
                logger.warning("- %s", err)
            final_markdown = pre_linted_md
    else:
        final_markdown = pre_linted_md
    
    return IssueFinal(
        markdown=final_markdown,
        word_count=len(final_markdown.split()),
        links_checked=False, # Link checking not implemented yet
    )
