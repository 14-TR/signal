import argparse
from pathlib import Path
import os

from signalai.pipeline import ingest, ranker, theme, draft, formatter, emitter
from signalai.llm import summarize, impacts
from signalai.llm.client import LLMClient
from signalai.config import load_settings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feeds", required=True)
    ap.add_argument("--store", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--llm-impacts", action="store_true", help="Use LLM to generate Predicted Impacts")
    ap.add_argument("--llm-summaries", action="store_true", help="Use LLM to generate one-line summaries")
    ap.add_argument("--no-format", action="store_true", help="Disable the LLM formatter and use the pre-linted version")
    args = ap.parse_args()

    # Load settings and initialize client
    settings = load_settings()
    if args.no_format:
        settings.formatter.enable = False
    
    # Override model from config if passed as arg, for convenience
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

    top_k = ranker.select(ranked_items, args.k, 3) # per_domain_cap should be in config

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
