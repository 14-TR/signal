# Reviewer Agent Spec (Formatter) — Signal.ai

## Purpose

Transform the raw draft newsletter into a clean, readable, and consistent Markdown issue without altering content semantics. The agent enforces structure, formatting, and brevity; it does not add or remove items.

---

## Inputs
	1.	**IssueDraft (structured)**
	•	`date`: YYYY-MM-DD
	•	`top_signals`: `list[Item]` where `Item` = `{title, url, source, summary, domain, published, signal}`
	•	`bullets`: `list[{item_ref, one_line_summary}]` (may be empty strings)
	•	`impacts_md`: `str` (LLM or rules-based)
	•	`themes`: `dict[str,bool]`
	2.	**Locked Reference List (for validation)**
	•	`refs`: `list[{title, url}]` extracted from `top_signals` (order preserved)
	3.	**StyleConfig**
	•	`wrap_col`: 100
	•	`grouping`: `["Research","Industry","Open Source","Commentary"]`
	•	`summary_len_words`: `[12, 38]`
	•	`section_sep`: '---'
	•	`require_summaries`: `true`
	•	`max_top_signals`: 14

---

## Output

`IssueFinal.markdown` (string) with this exact structure:

```markdown
# Signal.ai — <date>

## Top Signals

### Research
- Title [Site](URL)
  One-line summary wrapped to <wrap_col> chars.

### Industry
- ...
  ...

### Open Source
- ...
  ...

### Commentary
- ...
  ...

<section_sep>

## Predicted Impacts
- 3–5 bullets in Markdown (single sentence each; no links added)
```

---

## Hard Invariants (must never be violated)
-	No additions/removals of Top Signal items.
-	No changes to any title text or URL strings.
-	Order stability within each group equals the order of `top_signals` after grouping; cross-group order follows `grouping`.
-	No new links introduced anywhere.
-	No HTML; Markdown only.
-	Line wrapping ≤ `wrap_col`.

---

## Transformations (what the agent is allowed to do)
-	Normalize whitespace; strip HTML tags or HN metadata noise.
-	Ensure every item has exactly one indented one-line summary:
	-	Prefer provided `bullet.summary`.
	-	If empty or too short/long → rewrite concisely (1 line; 12–38 words).
-	Group items by simple rules:
	-	**Research**: domains `arxiv.org`, `research.google`, `openreview.net`, obvious research posts on lab blogs.
	-	**Industry**: lab/product blogs (OpenAI, Anthropic, Meta AI, Google AI).
	-	**Open Source**: `github.com`, `pypi.org`, repo releases.
	-	**Commentary**: news/analyst/blog/HN posts not covered above.
-	Insert `section_sep` before Predicted Impacts.
-	Optionally rewrite Impacts bullets for clarity/conciseness without adding links.

---

## Pre-Lint (deterministic, before LLM)
1.	**Clean summaries**:
	-	Strip HTML tags, remove “Article URL/Comments URL/Points/# Comments”.
	-	Collapse whitespace; unescape common HTML entities.
2.	**Clamp & normalize**:
	-	Truncate titles to 110 chars with … (but keep original in refs list).
	-	Ensure summary word count in `[12, 38]`; else mark `needs_rewrite`.
3.	**Grouping** by domain rules above; items that don’t match fall back to **Commentary**.
4.	Assemble **Draft Markdown** in target structure with placeholder summaries where needed (`[rewrite required]`).

---

## LLM Prompt (Reviewer Agent)

### System

You are a precise newsletter formatter. You must:
	1.	Keep the same items, titles, and URLs (do not add, remove, or alter them).
	2.	Produce clean Markdown only—no HTML.
	3.	Use the given section order and grouping.
	4.	For each Top Signal: one title line and one single-line summary (12–38 words), neutral and journalistic.
	5.	Wrap lines to `{wrap_col}` columns; insert a blank line between bullets.
	6.	Do not introduce any new links, footnotes, or emojis.

### User

```
# INPUT: LOCKED REFS (DO NOT CHANGE)
<refs_json>

# INPUT: DRAFT (CLEANUP & REFORMAT ONLY)
<draft_markdown>

# TASK
- Reformat the draft into the final house style.
- Where a summary is poor or marked [rewrite required], rewrite it concisely (12–38 words).
- Keep titles and URLs exactly as in LOCKED REFS.
- Group sections as shown; insert '---' before "## Predicted Impacts".
- Output only the final Markdown.
```

(Pass `refs_json` as JSON array; pass `draft_markdown` as fenced code or block for clarity.)

---

## Post-Validation (deterministic, after LLM)
-	**Refs check**:
	-	Extract `(title,url)` pairs from the output; must match input `refs` exactly (order-agnostic across groups but length and set equality required).
	-	**Link integrity**: all URLs present and unchanged.
	-	**No extra links**: count of markdown links equals count in `refs` + count in Impacts (should be zero in Impacts).
-	**Style checks**:
	-	Every bullet has exactly one following summary line.
	-	Word count for each summary in `[12, 38]`.
	-	No HTML tags present.
	-	Lines ≤ `wrap_col`.
-	If any check fails → fallback to pre-linted draft and append a warning banner at the top:
> Formatting agent failed validation; showing pre-linted version.

---

## Failure Modes & Handling
-	**LLM timeout/error** → use pre-linted draft; log `formatter.llm_error`.
-	**Validation fail** → use pre-linted draft; log specific failure(s).
-	**Excess length** → drop trailing non-critical whitespace, then re-wrap; if still long, accept but warn.

---

## Interfaces (to implement later)

`pipeline/formatter.py`
-	`def pre_lint(draft: IssueDraft, cfg: StyleConfig) -> str`
-	`def llm_format(pre_linted_md: str, refs: list[dict], cfg: StyleConfig) -> str`
-	`def validate(final_md: str, refs: list[dict], cfg: StyleConfig) -> tuple[bool, list[str]]`
-	`def format_issue(draft: IssueDraft, cfg: StyleConfig, client: LLMClient) -> str`
-	Flow: `pre_lint` → `llm_format` → `validate` → (`ok` ? `final` : `pre_linted`)

`llm/reformat.py`
-	`def run(pre_linted_md: str, refs_json: str, cfg: StyleConfig, client: LLMClient) -> str`

`llm/client.py`
-	`class LLMClient: def chat(self, messages, model, temperature, max_tokens, timeout) -> str`

---

## Config Defaults

```toml
[style]
wrap_col = 100
grouping = ["Research","Industry","Open Source","Commentary"]
summary_min_words = 12
summary_max_words = 38
section_sep = "---"
require_summaries = true

[formatter]
enable = true
model = "gpt-4o-mini"
temperature = 0.2
max_tokens = 1200
timeout_s = 60
```

---

## Acceptance Tests
1.	**Link Preservation**: output contains all and only input URLs; titles unchanged.
2.	**Uniform Bullets**: each bullet has one summary line; word counts in bounds.
3.	**Grouping**: items routed to expected sections given their domains.
4.	**Readability**: no HTML; line lengths ≤ `wrap_col`; sections separated by `---`.
5.	**Impacts Integrity**: impacts retained (optionally reworded) with no links added.

---

## Execution Plan (short-term)
-	Implement `formatter.py` with pre-lint + LLM + post-validate.
-	Add `--format` flag to CLI to enable formatter; default on.
-	Log validation outcomes; keep the pre-linted fallback reliable.
-	Iterate on prompt with a small few-shot (optional) once the validator is stable.
