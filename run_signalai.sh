#!/usr/bin/env bash
# Usage: ./run_signalai.sh
# Runs the SignalAI CLI with default configuration files.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
python -m signalai.cli run --feeds feeds.json --store sources.json --out out/
