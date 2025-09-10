#!/usr/bin/env python3
"""
Signal.ai Stage-1 Newsletter Generator

Minimal pipeline:
- Load feeds.json
- Fetch entries (RSS, GitHub releases, Arxiv)
- Normalize + dedupe against sources.json
- Rank by signal score
- Emit newsletter_<YYYY-MM-DD>.md
"""

import argparse
import json
import hashlib
import os
import sys
import datetime
import requests
import feedparser
from pathlib import Path
from urllib.parse import urlparse
import textwrap

# ----------------------------
# Authority/keyword config & helpers
# ----------------------------
AUTHORITY = {
    "openai.com": 1.0,
    "deepmind.google": 0.95,
    "anthropic.com": 0.95,
    "arxiv.org": 0.85,
    "github.com": 0.90,
    "huggingface.co": 0.90,
    "research.google": 0.95,
    "ai.facebook.com": 0.90,
}

BOOST_TERMS = [
    "agent", "agents", "retrieval", "evaluation", "eval", "multimodal",
    "safety", "inference", "latency", "throughput", "tokenization",
    "memory", "orchestration", "pruning", "distillation", "long context"
]

def domain_of(url: str) -> str:
    try:
        d = urlparse(url).netloc or ""
        return d.replace("www.", "")
    except Exception:
        return ""


def site_label(url: str, fallback: str) -> str:
    d = domain_of(url)
    if "arxiv.org" in d: return "arXiv"
    if "github.com" in d: return "GitHub"
    if "openai.com" in d: return "OpenAI"
    if "deepmind.google" in d: return "DeepMind"
    if "anthropic.com" in d: return "Anthropic"
    if "huggingface.co" in d: return "HF"
    return fallback or (d if d else "source")


def clamp_title(s: str, n: int = 110) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"

# ----------------------------
# LLM impacts generation (optional)
# ----------------------------

def generate_impacts_llm(items, model: str = None, max_words: int = 180) -> str:
    """Use an LLM to write the Predicted Impacts section in Markdown bullets.
    Reads OPENAI_API_KEY (and optional OPENAI_BASE_URL, SIGNALAI_LLM_MODEL).
    Returns empty string on failure to allow fallback.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return ""
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = model or os.getenv("SIGNALAI_LLM_MODEL", "gpt-4o-mini")

    # Compact digest of sources to keep prompt small
    def fmt(it):
        title = (it.get("title") or "").strip()
        src = it.get("source") or domain_of(it.get("url", ""))
        url = it.get("url", "")
        summ = (it.get("summary") or "").strip().replace("\n", " ")
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
        f"Limit to about {max_words} words total.\n\nTop Signals:\n{sources_block}"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.3,
        "max_tokens": 400,
    }

    try:
        resp = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        return content
    except Exception:
        return ""


# ----------------------------
# LLM per-item summary (optional)
# ----------------------------

def summarize_item_llm(item, model: str = None, max_words: int = 30) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return ""
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = model or os.getenv("SIGNALAI_LLM_MODEL", "gpt-4o-mini")

    title = (item.get("title") or "").strip()
    src = item.get("source") or domain_of(item.get("url", ""))
    url = item.get("url", "")
    summ = (item.get("summary") or "").strip().replace("\n", " ")
    if len(summ) > 600:
        summ = summ[:597].rstrip() + "…"

    system_msg = (
        "You are a copy editor. Write a single-line, neutral, journalistic synopsis under "
        f"{max_words} words. No fluff. Start directly with the finding or action."
    )
    user_msg = f"Title: {title}\nSource: {src}\nURL: {url}\nExisting summary (may be poor): {summ}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.2,
        "max_tokens": 120,
    }

    try:
        resp = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=45,
        )
        resp.raise_for_status()
        content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        content = " ".join(content.split())
        words = content.split()
        if len(words) > max_words:
            content = " ".join(words[:max_words]) + "…"
        return content
    except Exception:
        return ""

# ----------------------------
# Utility functions
# ----------------------------

def sha1_of(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()

def load_json(path: Path, default):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path: Path, obj):
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    tmp.replace(path)

def canonicalize_url(url: str) -> str:
    return url.split("?")[0].strip().lower()

# ----------------------------
# Fetchers
# ----------------------------

def fetch_rss(feed):
    parsed = feedparser.parse(feed["url"])
    items = []
    for entry in parsed.entries:
        items.append({
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "summary": entry.get("summary", "")[:500],
            "published": entry.get("published", datetime.datetime.utcnow().isoformat() + "Z"),
            "tags": [],
            "source": feed["name"]
        })
    return items

def fetch_github_releases(feed):
    r = requests.get(feed["url"], timeout=15)
    r.raise_for_status()
    releases = r.json()
    items = []
    for rel in releases[:10]:
        items.append({
            "title": rel.get("name") or rel.get("tag_name", ""),
            "url": rel.get("html_url", ""),
            "summary": (rel.get("body") or "")[:500],
            "published": rel.get("published_at", datetime.datetime.utcnow().isoformat() + "Z"),
            "tags": ["release"],
            "source": feed["name"]
        })
    return items

def fetch_arxiv(feed):
    parsed = feedparser.parse(feed["url"])
    items = []
    for entry in parsed.entries:
        items.append({
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "summary": entry.get("summary", "")[:500],
            "published": entry.get("published", datetime.datetime.utcnow().isoformat() + "Z"),
            "tags": ["arxiv"],
            "source": feed["name"]
        })
    return items

FETCHERS = {
    "rss": fetch_rss,
    "github_releases": fetch_github_releases,
    "arxiv": fetch_arxiv
}

# ----------------------------
# Ranking
# ----------------------------

def compute_signal(item):
    """Score = novelty + authority + keyword + engagement(prior)."""
    # Novelty: 1 within 72h, linear decay to 0 by 7 days
    novelty = 0.5
    try:
        dt = datetime.datetime.fromisoformat(item.get("published", "").replace("Z", ""))
        age_days = max(0.0, (datetime.datetime.utcnow() - dt).total_seconds() / 86400.0)
        if age_days <= 3:
            novelty = 1.0
        elif age_days <= 7:
            novelty = max(0.0, 1.0 - (age_days - 3) / 4.0)
        else:
            novelty = 0.0
    except Exception:
        pass

    # Authority by domain
    dom = domain_of(item.get("url", ""))
    authority = AUTHORITY.get(dom, 0.6)

    # Keyword match
    text = (item.get("title", "") + " " + item.get("summary", "")).lower()
    kw_hits = sum(1 for kw in BOOST_TERMS if kw in text)
    keyword = min(1.0, kw_hits / 4.0)  # saturate quickly

    # Engagement proxy: small prior; bump for GitHub
    engagement = 0.3 + (0.15 if "github.com" in dom else 0.0)

    return 0.35 * novelty + 0.30 * authority + 0.25 * keyword + 0.10 * engagement

# ----------------------------
# Main pipeline
# ----------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feeds", required=True)
    ap.add_argument("--store", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--llm-impacts", action="store_true", help="Use LLM to generate Predicted Impacts")
    ap.add_argument("--model", default=None, help="LLM model (default SIGNALAI_LLM_MODEL or gpt-4o-mini)")
    ap.add_argument("--impacts-max-words", type=int, default=180, help="Word budget for LLM impacts")
    ap.add_argument("--llm-summaries", action="store_true", help="Use LLM to generate one-line summaries under each Top Signal")
    ap.add_argument("--summary-max-words", type=int, default=30, help="Word budget per summary line")
    args = ap.parse_args()

    feeds = load_json(Path(args.feeds), [])
    store = load_json(Path(args.store), [])
    seen_hashes = {r.get("hash") for r in store}

    new_items = []
    for feed in feeds:
        ftype = feed.get("type")
        fetcher = FETCHERS.get(ftype)
        if not fetcher:
            print(f"Unknown feed type: {ftype}", file=sys.stderr)
            continue
        try:
            entries = fetcher(feed)
        except Exception as e:
            print(f"Fetch error for {feed['name']}: {e}", file=sys.stderr)
            continue
        for e in entries:
            url = canonicalize_url(e["url"])
            h = sha1_of(url)
            e["hash"] = h
            if h not in seen_hashes:
                new_items.append(e)
                seen_hashes.add(h)

    # Extend store
    store.extend(new_items)
    save_json(Path(args.store), store)

    # Rank
    for it in store:
        it["signal"] = compute_signal(it)
    ranked = sorted(store, key=lambda x: (x["signal"], x.get("published", "")), reverse=True)

    # Cap per-domain to avoid a single-source flood (e.g., arXiv)
    per_domain_cap = 3
    picked, perdom = [], {}
    for it in ranked:
        d = domain_of(it.get("url", ""))
        if perdom.get(d, 0) >= per_domain_cap:
            continue
        picked.append(it)
        perdom[d] = perdom.get(d, 0) + 1
        if len(picked) >= args.k:
            break

    topk = picked

    # Emit Markdown
    today = datetime.date.today().isoformat()
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    mdpath = outdir / f"newsletter_{today}.md"

    lines = []
    lines.append(f"# Signal.ai — {today}\n")
    lines.append("## Top Signals")
    for it in topk:
        site = site_label(it.get("url", ""), it.get("source", ""))
        title = clamp_title(it.get("title", "").strip())
        lines.append(f"- {title} [{site}]({it['url']})")

        # one-line summary: prefer decent feed summary; else LLM if enabled; else skip
        feed_sum = (it.get("summary") or "").strip().replace("\n", " ")
        feed_sum = " ".join(feed_sum.split())
        wc = len(feed_sum.split())
        summary_line = ""
        if 12 <= wc <= 38:
            summary_line = feed_sum
        elif args.llm_summaries:
            summary_line = summarize_item_llm(it, model=args.model, max_words=args.summary_max_words)

        if summary_line:
            wrapped = textwrap.fill(summary_line, width=100, subsequent_indent="  ")
            lines.append(f"  {wrapped}")
    lines.append("")

    # Simple theme extraction for impacts
    text_join = lambda it: (it.get("title", "") + " " + it.get("summary", "")).lower()
    cat = lambda keys: any(any(k in text_join(it) for k in keys) for it in topk)

    themes = {
        "Agents & Orchestration": cat(["agent", "orchestr"]),
        "Model Efficiency (Pruning/Distill/Latency)": cat(["pruning", "distill", "latency", "throughput"]),
        "Evaluation & QA": cat(["evaluation", "eval", "benchmark"]),
        "Multimodal & VLM": cat(["multimodal", "vision", "vlm", "image"]),
        "Safety & Alignment": cat(["safety", "alignment", "rlhf", "dpo"]),
    }

    lines.append("## Predicted Impacts")
    llm_md = ""
    if args.llm_impacts:
        llm_md = generate_impacts_llm(topk, model=args.model, max_words=args.impacts_max_words)

    if llm_md:
        lines.append(llm_md)
    else:
        if not any(themes.values()):
            lines.append("Near-term: incremental research updates with limited ops impact; reassess next run.")
        else:
            if themes["Agents & Orchestration"]:
                lines.append("- Teams shipping agent workflows can expect **higher ROI from tool-use and attribution methods**; prioritize evals that measure end-task completion, not just reasoning tokens.")
            if themes["Model Efficiency (Pruning/Distill/Latency)"]:
                lines.append("- **Cost and latency will drop** for common inference paths; revisit batch sizes and concurrency limits to unlock cheaper throughput on commodity GPUs/CPUs.")
            if themes["Evaluation & QA"]:
                lines.append("- **Stronger eval hygiene** will pressure product teams to publish metrics; add canary tasks and failure attribution to your CI for LLM features.")
            if themes["Multimodal & VLM"]:
                lines.append("- **VLM roadmaps**: expect better instruction-following on vision tasks; budget for dataset curation and prompt-tuning rather than immediate model swaps.")
            if themes["Safety & Alignment"]:
                lines.append("- **Policy + preference optimization** advances imply tighter feedback loops; ensure red-team checklists and post-deployment monitoring are in place.")
    lines.append("")

    with open(mdpath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote newsletter to {mdpath} with {len(topk)} items.")

if __name__ == "__main__":
    main()