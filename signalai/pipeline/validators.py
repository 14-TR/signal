import re
from typing import List, Tuple, Dict
from ..models import Item
from ..config import StyleConfig

def _extract_links_and_titles(markdown: str) -> List[Dict[str, str]]:
    """Extracts a list of {"title": title, "url": url} from markdown."""
    # Pattern to find markdown links and the text immediately preceding them
    pattern = re.compile(r'- ([^\[\]]+)\[[^\[\]]+\]\((https?://[^\s\)]+)\)')
    matches = pattern.findall(markdown)
    return [{"title": title.strip(), "url": url} for title, url in matches]

def validate(
    final_md: str,
    original_items: List[Item],
    cfg: StyleConfig
) -> Tuple[bool, List[str]]:
    """
    Performs a comprehensive validation of the final markdown output.
    Returns a tuple of (is_valid, list_of_errors).
    """
    errors = []
    
    # 1. Refs check: Link and Title Preservation
    original_refs = {item.url: item.title.strip() for item in original_items}
    output_links = _extract_links_and_titles(final_md)
    output_urls = {link['url'] for link in output_links}

    if len(output_links) != len(original_items):
        errors.append(f"Validation Error: Item count mismatch. Expected {len(original_items)}, found {len(output_links)}.")

    for url, title in original_refs.items():
        if url not in output_urls:
            errors.append(f"Validation Error: Missing URL: {url}")

    # 2. No extra links
    total_links = len(re.findall(r'https?://', final_md))
    if total_links > len(original_refs):
        errors.append("Validation Error: Extra links were introduced in the output.")

    # 3. Style checks
    lines = final_md.split('\n')
    in_top_signals = False
    for i, line in enumerate(lines):
        if line.startswith("## Top Signals"):
            in_top_signals = True
        if line.startswith("## Predicted Impacts") or line.strip() == cfg.section_sep:
            in_top_signals = False
            continue # Don't process the separator as an item

        if in_top_signals and line.strip().startswith("-"):
            if i + 1 >= len(lines) or not lines[i+1].strip():
                errors.append(f"Validation Error: Missing summary for item: {line}")
            else:
                summary_line = lines[i+1].strip()
                if summary_line == "[rewrite required]":
                    continue # This is a valid placeholder, not an error
                word_count = len(summary_line.split())
                if not (cfg.summary_min_words <= word_count <= cfg.summary_max_words):
                    errors.append(f"Validation Error: Summary word count out of bounds ({word_count}) for item: {line}")

        # Limit line length check to content sections
        if in_top_signals and len(line) > cfg.wrap_col:
            errors.append(f"Validation Error: Line exceeds {cfg.wrap_col} characters: '{line[:cfg.wrap_col]}...'")

    if "<" in final_md and "a href" in final_md.lower():
        errors.append("Validation Error: Potential HTML tags found in output.")

    is_valid = not errors
    return is_valid, errors
