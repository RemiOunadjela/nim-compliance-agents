"""YAML framework definition loader."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel

_FRAMEWORKS_DIR = Path(__file__).parent


class ViolationCategory(BaseModel):
    """A single violation category within a regulatory framework."""

    id: str
    name: str
    article: str
    description: str
    severity_baseline: str


class FrameworkDefinition(BaseModel):
    """Parsed regulatory framework definition."""

    name: str
    abbreviation: str
    jurisdiction: str
    version: str
    violation_categories: list[ViolationCategory]
    severity_scale: dict[str, str]


def load_framework(name: str) -> FrameworkDefinition:
    """Load a framework definition from its YAML file.

    Args:
        name: Framework identifier (e.g., "dsa"). Must correspond to a
              YAML file in the frameworks directory.

    Returns:
        Parsed framework definition.

    Raises:
        FileNotFoundError: If the framework YAML does not exist.
        ValueError: If the YAML is malformed.
    """
    path = _FRAMEWORKS_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Framework '{name}' not found at {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    return FrameworkDefinition(**data)


def list_frameworks() -> list[str]:
    """Return the names of all available framework definitions."""
    return sorted(p.stem for p in _FRAMEWORKS_DIR.glob("*.yaml"))
