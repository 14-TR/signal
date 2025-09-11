import argparse
import datetime
import os
import subprocess
from pathlib import Path
from typing import List

from pydantic import ValidationError

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


def _run(args: argparse.Namespace) -> None:
    """Run the signal pipeline."""
    settings = load_settings()
    if args.no_format:
        settings.formatter.enable = False

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
        client=client,
    )

    emitter.write(final_issue, Path(args.out))


def _edit_config(args: argparse.Namespace) -> None:
    """Open the config file in an editor and validate it."""
    config_path = args.path or Path(__file__).with_name("config.toml")
    editor = os.getenv("EDITOR", "vi")
    subprocess.call([editor, str(config_path)])

    try:
        load_settings(config_path)
        print("Configuration valid")
    except ValidationError as e:
        print("Configuration invalid:\n", e)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the signal pipeline")
    run.add_argument("--feeds", required=True)
    run.add_argument("--store", required=True)
    run.add_argument("--out", required=True)
    run.add_argument("--k", type=int, default=10)
    run.add_argument("--llm-impacts", action="store_true", help="Use LLM to generate Predicted Impacts")
    run.add_argument("--llm-summaries", action="store_true", help="Use LLM to generate one-line summaries")
    run.add_argument("--no-format", action="store_true", help="Disable the LLM formatter and use the pre-linted version")
    run.add_argument("--window-days", type=int, default=3, help="Only consider items published within the last N days (0 = no limit)")
    pref_group = run.add_mutually_exclusive_group()
    pref_group.add_argument("--prefer-new", dest="prefer_new", action="store_true", help="Rank new items first within the window (default)")
    pref_group.add_argument("--no-prefer-new", dest="prefer_new", action="store_false", help="Do not prioritize newly ingested items")
    run.set_defaults(prefer_new=True)
    run.add_argument("--only-new", action="store_true", help="Only consider items newly ingested this run")
    run.set_defaults(func=_run)

    cfg = sub.add_parser("config", help="Edit and validate the configuration file")
    cfg.add_argument("--path", type=Path, help="Path to config file", default=None)
    cfg.set_defaults(func=_edit_config)

    return ap


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
