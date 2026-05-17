"""Manifest schema validation. Surfaces friendly errors with JSON pointer paths."""
from __future__ import annotations
import json
from importlib.resources import files
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator


class ManifestValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("\n  - ".join(["manifest validation failed:", *errors]))


def _load_schema() -> dict[str, Any]:
    path = files("agent_init.schema").joinpath("manifest.schema.json")
    return json.loads(path.read_text())


def validate(manifest: dict, manifest_path: Path | None = None) -> None:
    """Validate a parsed manifest dict. Raises ManifestValidationError on failure."""
    validator = Draft202012Validator(_load_schema())
    errors = sorted(validator.iter_errors(manifest), key=lambda e: e.absolute_path)
    if not errors:
        return

    formatted: list[str] = []
    for e in errors:
        ptr = "$" + "".join(
            f"[{p}]" if isinstance(p, int) else f".{p}" for p in e.absolute_path
        )
        formatted.append(f"{ptr}: {e.message}")
    raise ManifestValidationError(formatted)


__all__ = ["validate", "ManifestValidationError"]
