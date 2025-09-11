# Plugin registry for Source implementations.
from importlib import import_module, metadata
from typing import Dict, List, Optional, Type

from .base import Source


registry: Dict[str, Type[Source]] = {}


def register(cls: Type[Source]) -> Type[Source]:
    """Class decorator to register a :class:`Source` implementation."""
    name = getattr(cls, "NAME", cls.__name__.lower())
    registry[name] = cls
    return cls


def load_plugins(config: Optional[List[str]] = None) -> None:
    """Load plugins from entry points or a config list of dotted paths.

    Args:
        config: Optional list of ``"module:Class"`` strings to import.
    """
    for ep in metadata.entry_points(group="signalai.sources"):
        cls = ep.load()
        register(cls)

    if config:
        for path in config:
            module_name, class_name = path.split(":")
            module = import_module(module_name)
            cls = getattr(module, class_name)
            register(cls)


# Import built-in sources so they register themselves.
from . import rss as _rss  # noqa: F401
from . import github as _github  # noqa: F401
from . import arxiv as _arxiv  # noqa: F401

__all__ = ["Source", "register", "load_plugins", "registry"]

