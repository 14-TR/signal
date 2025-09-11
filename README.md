# Signal.ai

Signal.ai automates the creation of an AI-focused newsletter. It ingests items from configured feeds, ranks them by signal strength, and emits a formatted Markdown issue.

## Installation

1. Clone the repository.
2. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run the CLI module with paths to your feeds, store, and output dir:

```bash
python -m signalai.cli --feeds feeds.json --store sources.json --out out/ --k 10
```

Optional flags:

- `--llm-summaries` to use an LLM for bullet summaries.
- `--llm-impacts` to generate a Predicted Impacts section with an LLM.
- `--no-format` to disable the LLM formatter and use the pre-linted version.
- `--window-days N` limit candidates to the last N days (default: 3; 0 = no limit).
- `--prefer-new` prioritize items newly ingested this run (default).
- `--no-prefer-new` disable the new-item preference.
- `--only-new` only consider items newly ingested this run.

### Professional run example

```bash
export OPENAI_API_KEY=... \
&& export SIGNALAI_LLM_MODEL=gpt-5-mini \
&& python -m signalai.cli \
  --feeds feeds.json \
  --store sources.json \
  --out out/ \
  --k 12 \
  --window-days 3 \
  --prefer-new \
  --llm-summaries \
  --llm-impacts
```

## Configuration

Runtime configuration lives in `signalai/config.py`. Default `StyleConfig` options include line wrapping, section grouping, summary length bounds, and maximum number of signals. `FormatterConfig` toggles LLM formatting and controls model, temperature, token limits, and timeout. Set the `SIGNALAI_LLM_MODEL` environment variable to override the LLM model at runtime.

## Source plugins

Custom feed sources implement the `Source` interface defined in `signalai/sources/base.py`. A source provides `fetch` and `parse` methods and may optionally override `dedupe`.

Use the `register` decorator so your plugin is available through the registry:

```python
from signalai.sources import Source, register

@register
class MySource(Source):
    NAME = "my_source"

    def fetch(self, feed_cfg):
        ...

    def parse(self, raw, feed_cfg):
        ...
```

Plugins can be discovered dynamically either via entry points named `signalai.sources` or by passing dotted paths to `load_plugins`:

```python
from signalai.sources import load_plugins

load_plugins(["path.to.module:MySource"])
```

## Documentation

See the [Stage‑1 engineering spec](docs/signal-spec-stage-1.md), [reviewer agent spec](docs/reviewer-agent-spec.md), and [status synopsis](docs/status-synopsis.md) for deeper context and design details.
