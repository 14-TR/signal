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

Run the CLI module with paths to your feeds, store, and output file:

```bash
python -m signalai.cli --feeds feeds.json --store sources.json --out out/newsletter.md --k 10
```

Optional flags:

- `--llm-summaries` to use an LLM for bullet summaries.
- `--llm-impacts` to generate a Predicted Impacts section with an LLM.
- `--no-format` to disable the LLM formatter and use the pre-linted version.

## Configuration

Runtime configuration lives in `signalai/config.py`. Default `StyleConfig` options include line wrapping, section grouping, summary length bounds, and maximum number of signals. `FormatterConfig` toggles LLM formatting and controls model, temperature, token limits, and timeout. Set the `SIGNALAI_LLM_MODEL` environment variable to override the LLM model at runtime.

## Documentation

See the [Stage‑1 engineering spec](docs/signal-spec-stage-1.md), [reviewer agent spec](docs/reviewer-agent-spec.md), and [status synopsis](docs/status-synopsis.md) for deeper context and design details.
