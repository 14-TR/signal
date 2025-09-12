# Signal.ai — Stage‑1 Engineering Specification

Version: 1.0  
Date: 2025-09-08  
Owner: TR Ingram (Signal.ai)

## 1. Objective and Scope
Build a minimal, reliable pipeline that gathers AI-related sources, ranks them by signal strength, and emits a tightly written Markdown newsletter every 2–3 days. Stage 1 uses only JSON storage, one Python CLI, and Windows Task Scheduler. No external DB or cloud services.

## 2. Success Criteria
- Automated input: fetch from configured feeds without manual steps.
- Persistence: append normalized records to `sources.json` with deterministic dedupe.
- Ranking: compute signal score and return at least 8–12 high-signal items per run.
- Output: create `out/newsletter_<YYYY-MM-DD>.md` with two sections: Top Signals and Predicted Impacts.
- Reliability: exit code 0 on success; non-zero on hard failures; write `logs/run_<timestamp>.log`.
- Idempotence: re-running the same day does not duplicate items or overwrite an existing newsletter file.

## 3. Inputs and Data Contracts
### 3.1 `feeds.json` (source configuration)
An array of objects with a strict `type`:
```json
[
  {"type": "rss", "name": "Anthropic", "url": "https://www.anthropic.com/news/rss.xml"},
  {"type": "rss", "name": "Cohere", "url": "https://txt.cohere.com/feed"},
  {"type": "rss", "name": "DeepMind", "url": "https://deepmind.google/discover/rss.xml"},
  {"type": "rss", "name": "EleutherAI", "url": "https://blog.eleuther.ai/rss/"},
  {"type": "rss", "name": "Google AI Blog", "url": "https://ai.googleblog.com/feeds/posts/default"},
  {"type": "rss", "name": "Hacker News AI", "url": "https://hnrss.org/newest?q=AI%20OR%20LLM%20OR%20agents"},
  {"type": "rss", "name": "Meta AI", "url": "https://ai.meta.com/blog/rss/"},
  {"type": "rss", "name": "Mistral AI", "url": "https://mistral.ai/feed.xml"},
  {"type": "rss", "name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml"},
  {"type": "rss", "name": "Stability AI", "url": "https://stability.ai/blog.rss"},
  {"type": "github_releases", "name": "HuggingFace Transformers", "url": "https://github.com/huggingface/transformers"},
  {"type": "github_releases", "name": "LangChain", "url": "https://github.com/langchain-ai/langchain"},
  {"type": "github_releases", "name": "Llama.cpp", "url": "https://github.com/ggerganov/llama.cpp"},
  {"type": "github_releases", "name": "vLLM", "url": "https://github.com/vllm-project/vllm"},
  {"type": "arxiv", "name": "arXiv cs.AI", "url": "https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=25"},
  {"type": "arxiv", "name": "arXiv cs.CL", "url": "https://export.arxiv.org/api/query?search_query=cat:cs.CL&sortBy=submittedDate&sortOrder=descending&max_results=25"},
  {"type": "arxiv", "name": "arXiv cs.LG", "url": "https://export.arxiv.org/api/query?search_query=cat:cs.LG&sortBy=submittedDate&sortOrder=descending&max_results=25"}
]
```

### 3.2 `sources.json` (normalized store)
Array of records. All fields required unless noted:
```json
{
  "title": "string",
  "url": "string",
  "summary": "string",
  "published": "YYYY-MM-DDTHH:mm:ssZ",
  "tags": ["string"],
  "source": "string",            
  "hash": "sha1-of-canonical-url"
}
```

### 3.3 Output file
`out/newsletter_<YYYY-MM-DD>.md` with the structure:
```
# Signal.ai — <YYYY-MM-DD>

## Top Signals
- <concise bullet with 1–2 sentences> [<site>]

## Predicted Impacts
<3–6 short paragraphs grouped by theme; concrete who/what/so-what>
```

## 4. System Architecture
Single Python CLI `signalai.py` wires four components:
1) Fetchers: rss | github_releases | arxiv.  
2) Normalizer: schema enforcement + URL canonicalization + `sha1(url)`.
3) Ranker: compute signal score and select top K.
4) Emitter: generate Markdown and write logs.

### 4.1 Repository layout (Stage 1)
```
signal/
  docs/
    signal-spec-stage-1.md
  feeds.json
  sources.json
  out/                # newsletter outputs
  logs/               # run logs
  signalai.py         # main CLI
  fetchers/
    rss_fetcher.py
    github_fetcher.py
    arxiv_fetcher.py
  rank/
    ranker.py
  emit/
    markdown.py
  scripts/
    run_signalai.ps1
```

## 5. Processing Pipeline
1. Load `feeds.json` and validate schema.
2. For each feed: fetch entries using the type-specific fetcher.
3. Normalize each entry to the record schema. Canonicalize URLs (strip UTM and fragments), compute `hash`.
4. Dedupe against `sources.json` using `hash` and `title` case-insensitive.
5. Score each candidate, sort by `signal` desc then `published` desc.
6. Select top K (default 10, bounds 8–12), ensure domain diversity (max 4 per domain).
7. Emit Markdown to `out/newsletter_<YYYY-MM-DD>.md` if not already present; otherwise write to `out/newsletter_<YYYY-MM-DD>_<HHmmss>.md`.
8. Append newly seen items to `sources.json` and write `logs/run_<timestamp>.log` with counts (fetched, new, kept) and timing.

## 6. Ranking Model
Final score formula:
```
signal = 0.35*novelty + 0.30*authority + 0.25*keyword + 0.10*engagement
```
- Novelty: 1.0 if published within 72h; linearly decays to 0 by 7 days.
- Authority: domain weight in [0.2, 1.0], with official lab blogs, primary papers, and first-party repos highest.
- Keyword: normalized count over title + summary; boost terms include: agent, retrieval, evaluation, long context, multimodal, safety, inference, latency, throughput, tokenization, memory, orchestration.
- Engagement (optional): HN points, GitHub stars, or similar scaled to [0,1] when available; default 0.3 if unknown.

## 7. CLI Contract
```
python signalai.py \
  --feeds feeds.json \
  --store sources.json \
  --out out \
  --k 10 \
  --min-words 600 \
  --max-words 1200 \
  --dry-run        # do everything except write outputs
```
Exit codes: 0 success, 2 partial (some fetch failures but output produced), 1 hard failure.

## 8. Scheduler (Windows)
Wrapper `scripts/run_signalai.ps1`:
```powershell
$ErrorActionPreference = "Stop"
$script = "C:\\path\\to\\signalai.py"
$venv = "C:\\path\\to\\venv\\Scripts\\python.exe"
$workdir = "C:\\path\\to\\signal"
Push-Location $workdir
& $venv $script --feeds feeds.json --store sources.json --out out
Pop-Location
```
Register task (every 3 days at 06:00):
```powershell
schtasks /Create /TN "SignalAI" /TR "powershell -ExecutionPolicy Bypass -File C:\\path\\to\\scripts\\run_signalai.ps1" /SC DAILY /MO 3 /ST 06:00
```
Manual trigger:
```powershell
schtasks /Run /TN "SignalAI"
```

## 9. Logging and Observability
- File: `logs/run_<timestamp>.log` contains start/end times, per-feed counts, dedupe stats, selected K, output filename, and warnings.
- Console: INFO-level progress. Use `--verbose` for per-item scoring breakdown.

## 10. Quality Gates and Acceptance Checks
- At least 6 items in Top Signals, at most 14.
- All links return HTTP 200 at emit time.
- No duplicate titles or URLs in a single issue.
- Impacts section contains at least 3 distinct themes.
- Word count between `--min-words` and `--max-words`.

## 11. Error Handling and Safeguards
- Network failure on a single feed does not abort the run. Log and continue.
- If zero items score above 0.4, emit a stub issue with a warning header and keep top 5 by score.
- Always back up `sources.json` to `sources.bak.json` before write.
- Atomic writes: write to temp file then rename.

## 12. Security and Compliance (Stage 1)
- No secrets required. If a GitHub token is added later, load from environment variable `GITHUB_TOKEN` and do not write it to logs.
- Validate and sanitize URLs. Do not fetch binary links.
- Respect robots.txt for any future HTML scraping additions.

## 13. Roadmap (Beyond Stage 1)
- Stage 2: SQLite or Postgres backend, domain authority table, per-topic weighting.
- Stage 3: Publish to Substack or Ghost via API; Notion export; Telegram or email digests.
- Stage 4: SaaS dashboard, search, user preferences, auth, and cloud deployment.

## 14. Deliverables
- `docs/signal-spec-stage-1.md` (this spec)
- `feeds.json`
- `sources.json`
- `signalai.py` and supporting modules (`fetchers/`, `rank/`, `emit/`)
- `scripts/run_signalai.ps1`
- `out/` and `logs/` directories with artifacts
