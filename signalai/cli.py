import argparse
from pathlib import Path
import os
import datetime
from typing import List

from signalai.pipeline import ingest, ranker, theme, draft, formatter, emitter
from signalai.llm import summarize, impacts
from signalai.llm.client import LLMClient
from signalai.config import load_settings
from signalai.models import Item
from signalai.logging import get_logger


logger = get_logger(__name__)


def _filter_and_order_candidates(
    ranked_items: List[Item],
    new_items: List[Item],
    window_days: int,
    prefer_new: bool,
    only_new: bool,
) -> List[Item]:
    """Build the candidate pool based on recency and novelty preferences.

    - If only_new: take ranked new items only.
    - Else, start from items within the window (if window_days>0) else all.
      If prefer_new, place new items first (preserving rank), then fill with recent non-new.
    - If the window is too restrictive and yields nothing, fall back to all ranked items.
    """
    new_hashes = {it.hash for it in new_items if it.hash}

    # Build recency-filtered list
    if window_days and window_days > 0:
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff = now - datetime.timedelta(days=window_days)
        recent = [it for it in ranked_items if (it.published.tzinfo and it.published >= cutoff) or (not it.published.tzinfo and it.published.replace(tzinfo=datetime.timezone.utc) >= cutoff)]
    else:
        recent = list(ranked_items)

    if only_new:
        pool = [it for it in ranked_items if it.hash in new_hashes]
        if not pool:
            logger.info("No new items found; falling back to recent window (%s days)", window_days)
            pool = recent
        return pool

    if prefer_new:
        new_first = [it for it in recent if it.hash in new_hashes]
        rest = [it for it in recent if it.hash not in new_hashes]
        pool = new_first + rest
    else:
        pool = recent

    if not pool:
        logger.info("No items in recent window; falling back to all ranked items")
        pool = ranked_items

    return pool


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feeds", required=True)
    ap.add_argument("--store", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--llm-impacts", action="store_true", help="Use LLM to generate Predicted Impacts")
    ap.add_argument("--llm-summaries", action="store_true", help="Use LLM to generate one-line summaries")
    ap.add_argument("--no-format", action="store_true", help="Disable the LLM formatter and use the pre-linted version")
    # New selection controls
    ap.add_argument("--window-days", type=int, default=3, help="Only consider items published within the last N days (0 = no limit)")
    pref_group = ap.add_mutually_exclusive_group()
    pref_group.add_argument("--prefer-new", dest="prefer_new", action="store_true", help="Rank new items first within the window (default)")
    pref_group.add_argument("--no-prefer-new", dest="prefer_new", action="store_false", help="Do not prioritize newly ingested items")
    ap.set_defaults(prefer_new=True)
    ap.add_argument("--only-new", action="store_true", help="Only consider items newly ingested this run")
    args = ap.parse_args()

    # Load settings and initialize client
    settings = load_settings()
    if args.no_format:
        settings.formatter.enable = False
    
    # Override model from config if passed as env var
    llm_model_override = os.getenv("SIGNALAI_LLM_MODEL")
    if llm_model_override:
        settings.formatter.model = llm_model_override

    client = LLMClient(
        model=settings.formatter.model,
        temperature=settings.formatter.temperature,
        max_completion_tokens=settings.formatter.max_completion_tokens,
        timeout=settings.formatter.timeout_s,
    )

    all_items, new_items = ingest.run(Path(args.feeds), Path(args.store))

    for it in all_items:
        it.signal = ranker.score(it)

    ranked_items = sorted(all_items, key=lambda x: (x.signal, x.published), reverse=True)

    # Apply candidate selection to reduce repetition
    candidates = _filter_and_order_candidates(
        ranked_items=ranked_items,
        new_items=new_items,
        window_days=args.window_days,
        prefer_new=args.prefer_new,
        only_new=args.only_new,
    )

    top_k = ranker.select(
        candidates,
        args.k,
        settings.style.per_domain_cap,
    )

    logger.info(
        "Selecting %d items (k=%d) from %d candidates | window_days=%s prefer_new=%s only_new=%s new_ingested=%d total_store=%d",
        len(top_k), args.k, len(candidates), args.window_days, args.prefer_new, args.only_new, len(new_items), len(all_items)
    )

    detected_themes = theme.detect(top_k)

    bullets = summarize.top_bullets(top_k, args.llm_summaries, client, settings.style)

    impacts_md = ""
    if args.llm_impacts:
        impacts_md = impacts.generate_impacts_llm(top_k, client)

    issue_draft = draft.build(
        top_items=top_k,
        bullets=bullets,
        impacts_md=impacts_md,
        themes=detected_themes,
    )

    final_issue = formatter.beautify(
        issue_draft,
        cfg=settings.style,
        formatter_cfg=settings.formatter,
        client=client
    )

    emitter.write(final_issue, Path(args.out))

if __name__ == "__main__":
    main()
