"""Adapter contract. All adapters implement render(); validate() is optional."""
from __future__ import annotations
from pathlib import Path
from typing import Protocol, runtime_checkable
from .ir import Project, RenderReport


@runtime_checkable
class Adapter(Protocol):
    name: str
    target_dir: str

    def render(self, project: Project, out: Path) -> RenderReport: ...


_REGISTRY: dict[str, Adapter] = {}


def register(adapter: Adapter) -> None:
    _REGISTRY[adapter.name] = adapter


def get(name: str) -> Adapter:
    if name not in _REGISTRY:
        raise KeyError(f"No adapter named {name!r}. Available: {list(_REGISTRY)}")
    return _REGISTRY[name]


def all_names() -> list[str]:
    return list(_REGISTRY)
