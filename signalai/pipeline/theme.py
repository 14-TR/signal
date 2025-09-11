"""Theme detection and clustering utilities."""

from __future__ import annotations

import math
import hashlib
import random
from datetime import datetime, timezone
from typing import Dict, List

from signalai.models import Item


# ---------------------------------------------------------------------------
# Embedding model
# ---------------------------------------------------------------------------

try:  # pragma: no cover - optional dependency
    from sentence_transformers import SentenceTransformer as _STModel  # type: ignore
except Exception:  # pragma: no cover - fallback used in tests

    class _STModel:
        """Very small fallback embedding model.

        Each sentence is tokenized by whitespace and hashed into a fixed size
        vector. This keeps the code lightweight while presenting the same
        interface as ``sentence-transformers``.
        """

        def encode(self, texts: List[str]) -> List[List[float]]:  # type: ignore
            dim = 32
            vectors: List[List[float]] = []
            for text in texts:
                vec = [0.0] * dim
                for token in text.lower().split():
                    idx = int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16) % dim
                    vec[idx] += 1.0
                norm = math.sqrt(sum(v * v for v in vec)) or 1.0
                vectors.append([v / norm for v in vec])
            return vectors


_MODEL: _STModel | None = None


def _get_model() -> _STModel:
    global _MODEL
    if _MODEL is None:
        _MODEL = _STModel()
    return _MODEL


def _embed_items(items: List[Item]) -> List[List[float]]:
    model = _get_model()
    texts = [f"{it.title} {it.summary}" for it in items]
    return model.encode(texts)


# ---------------------------------------------------------------------------
# K-means clustering with silhouette selection
# ---------------------------------------------------------------------------


def _euclid(a: List[float], b: List[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _mean(vecs: List[List[float]]) -> List[float]:
    n = len(vecs)
    if n == 0:
        return [0.0] * len(vecs[0])
    return [sum(v[i] for v in vecs) / n for i in range(len(vecs[0]))]


def _kmeans(vecs: List[List[float]], k: int, max_iter: int = 10) -> List[int]:
    random.seed(0)
    centers = [vecs[0]]
    while len(centers) < k:
        distances = [min(_euclid(v, c) ** 2 for c in centers) for v in vecs]
        total = sum(distances)
        r = random.random() * total
        upto = 0.0
        for vec, dist in zip(vecs, distances):
            upto += dist
            if upto >= r:
                centers.append(vec)
                break
    labels = [0] * len(vecs)
    for _ in range(max_iter):
        changed = False
        for idx, vec in enumerate(vecs):
            dists = [_euclid(vec, c) for c in centers]
            new_label = dists.index(min(dists))
            if labels[idx] != new_label:
                changed = True
                labels[idx] = new_label
        for j in range(k):
            members = [vec for vec, lbl in zip(vecs, labels) if lbl == j]
            if members:
                centers[j] = _mean(members)
        if not changed:
            break
    return labels


def _silhouette(vecs: List[List[float]], labels: List[int], k: int) -> float:
    n = len(vecs)
    if k <= 1 or n <= 1:
        return 0.0
    scores: List[float] = []
    for i in range(n):
        same = [vecs[j] for j in range(n) if labels[j] == labels[i] and i != j]
        a = sum(_euclid(vecs[i], v) for v in same) / len(same) if same else 0.0
        b = None
        for cluster in range(k):
            if cluster == labels[i]:
                continue
            other = [vecs[j] for j in range(n) if labels[j] == cluster]
            if not other:
                continue
            dist = sum(_euclid(vecs[i], v) for v in other) / len(other)
            if b is None or dist < b:
                b = dist
        b = b or 0.0
        max_ab = max(a, b)
        scores.append((b - a) / max_ab if max_ab > 0 else 0.0)
    return sum(scores) / len(scores)


def cluster(items: List[Item], k_min: int = 2, k_max: int = 5) -> Dict[str, List[Item]]:
    """Group items by semantic similarity and return labelled clusters."""

    vecs = _embed_items(items)
    if not vecs:
        return {}

    best_k, best_score, best_labels = 1, -1.0, [0] * len(vecs)
    for k in range(k_min, min(k_max, len(vecs)) + 1):
        labels = _kmeans(vecs, k)
        score = _silhouette(vecs, labels, k)
        if score > best_score:
            best_k, best_score, best_labels = k, score, labels

    clusters: Dict[str, List[Item]] = {}
    for idx in range(best_k):
        members = [it for it, lbl in zip(items, best_labels) if lbl == idx]
        if members:
            label = " ".join(members[0].title.split()[:2])
            clusters[label] = members
    return clusters


# ---------------------------------------------------------------------------
# Scheduled re-clustering
# ---------------------------------------------------------------------------


_LAST_CLUSTER: datetime | None = None
_CACHED_CLUSTERS: Dict[str, List[Item]] = {}


def refresh_themes(items: List[Item], interval_hours: int = 24) -> Dict[str, List[Item]]:
    """Re-cluster items if the interval has elapsed."""

    global _LAST_CLUSTER, _CACHED_CLUSTERS
    now = datetime.now(timezone.utc)
    if (
        _LAST_CLUSTER is None
        or (now - _LAST_CLUSTER).total_seconds() >= interval_hours * 3600
    ):
        _CACHED_CLUSTERS = cluster(items)
        _LAST_CLUSTER = now
    return _CACHED_CLUSTERS


# ---------------------------------------------------------------------------
# Keyword-based detection (legacy)
# ---------------------------------------------------------------------------


THEME_KEYWORDS = {
    "Agents & Orchestration": ["agent", "orchestr"],
    "Model Efficiency (Pruning/Distill/Latency)": [
        "pruning",
        "distill",
        "latency",
        "throughput",
    ],
    "Evaluation & QA": ["evaluation", "eval", "benchmark"],
    "Multimodal & VLM": ["multimodal", "vision", "vlm", "image"],
    "Safety & Alignment": ["safety", "alignment", "rlhf", "dpo"],
}


def detect(items: List[Item]) -> Dict[str, bool]:
    text_join = lambda it: (it.title + " " + it.summary).lower()
    cat = lambda keys: any(any(k in text_join(it) for k in keys) for it in items)

    themes = {name: cat(keywords) for name, keywords in THEME_KEYWORDS.items()}
    return themes

