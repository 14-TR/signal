#!/bin/bash
set -e
WORKDIR="/Users/tr/Desktop/signal"
cd "$WORKDIR"
python3 signalai.py --feeds feeds.json --store sources.json --out out/