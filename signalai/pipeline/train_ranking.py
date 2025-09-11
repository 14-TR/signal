from __future__ import annotations

import csv
import math
import pickle
from pathlib import Path
from typing import List, Tuple

LOG_PATH = Path(__file__).resolve().parents[2] / "out" / "ranker_log.csv"
MODEL_PATH = Path(__file__).resolve().parents[2] / "out" / "ranker_model.pkl"


def load_training_data() -> Tuple[List[List[float]], List[float]]:
    X: List[List[float]] = []
    y: List[float] = []
    if not LOG_PATH.exists():
        raise FileNotFoundError(f"No log file found at {LOG_PATH}")
    with LOG_PATH.open() as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            features = [
                1.0,  # intercept
                float(row["novelty"]),
                float(row["authority"]),
                float(row["keyword_hits"]),
                float(row["engagement"]),
            ]
            label = 1.0 if row.get("event") in {"open", "click"} else 0.0
            X.append(features)
            y.append(label)
    if not X:
        raise ValueError("No data available for training")
    return X, y


def train_model(epochs: int = 500, lr: float = 0.1) -> Path:
    X, y = load_training_data()
    n_features = len(X[0])
    weights = [0.0] * n_features
    m = len(X)
    for _ in range(epochs):
        grads = [0.0] * n_features
        for xi, yi in zip(X, y):
            z = sum(w * x for w, x in zip(weights, xi))
            pred = 1.0 / (1.0 + math.exp(-z))
            for j in range(n_features):
                grads[j] += (pred - yi) * xi[j]
        for j in range(n_features):
            weights[j] -= lr * grads[j] / m
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MODEL_PATH.open("wb") as fh:
        pickle.dump(weights, fh)
    return MODEL_PATH


if __name__ == "__main__":
    train_model()
