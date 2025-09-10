"""Storage helpers.

This module provides a small abstraction around persistent storage so the
underlying backend can be swapped (e.g. JSON files today, SQLite tomorrow).
It also adds simple backup rotation when writing to disk to safeguard data.
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import date, datetime
from typing import Any


def json_serial(obj: Any):
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class Storage(ABC):
    """Abstract storage backend."""

    @abstractmethod
    def load(self, path: Path, default: Any):
        """Load object from *path* or return *default* when missing."""

    @abstractmethod
    def save(self, path: Path, obj: Any):
        """Persist *obj* to *path*."""


def _rotate_backups(path: Path, keep: int = 5) -> None:
    """Rotate backups for ``path`` keeping at most ``keep`` previous versions."""
    if keep <= 0:
        return

    for i in range(keep - 1, 0, -1):
        src = path.with_suffix(path.suffix + f".bak{i - 1}")
        dst = path.with_suffix(path.suffix + f".bak{i}")
        if src.exists():
            src.replace(dst)

    bak0 = path.with_suffix(path.suffix + ".bak0")
    if path.exists():
        path.replace(bak0)


class JsonStorage(Storage):
    """JSON-file based storage backend."""

    def __init__(self, backups: int = 5) -> None:
        self.backups = backups

    def load(self, path: Path, default: Any):  # type: ignore[override]
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return default

    def save(self, path: Path, obj: Any) -> None:  # type: ignore[override]
        _rotate_backups(path, self.backups)
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False, default=json_serial)
        tmp.replace(path)


# Default storage backend used by the application
_storage: Storage = JsonStorage()


def load(path: Path, default: Any):
    """Load data using the configured storage backend."""
    return _storage.load(path, default)


def save(path: Path, obj: Any) -> None:
    """Save data using the configured storage backend."""
    _storage.save(path, obj)


# Backwards compatibility for existing imports
load_json = load
save_json = save

