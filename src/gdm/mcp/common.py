"""Shared helpers for the GDM MCP server.

These helpers are used by the per-module tool definitions under ``gdm.mcp.tools``
and keep the ``system_path``/``model_ref`` XOR resolution and JSON-safe
serialization conventions in one place.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

from dist_stack.registry import resolve_model_ref
from gdm.distribution import DistributionSystem
from pint import Quantity


def _resolve_model_ref_to_path(model_ref: dict[str, Any]) -> str:
    """Resolve a model_ref payload to a concrete system JSON path.

    Path-carrying refs pass through; model_id/version resolve via the
    dist_stack model registry (DIST_STACK_MODEL_REGISTRY_DB).
    """
    return resolve_model_ref(model_ref)


def _get_system_path_arg(args: dict[str, Any]) -> str:
    """Extract system path from legacy system_path or model_ref input."""
    if isinstance(args.get("system_path"), str) and args["system_path"].strip():
        return str(args["system_path"])

    model_ref = args.get("model_ref")
    if isinstance(model_ref, dict):
        return _resolve_model_ref_to_path(model_ref)

    raise ValueError("Expected either 'system_path' or 'model_ref'")


def _system_path_arg(system_path: str | None, model_ref: dict[str, Any] | None) -> str:
    """Resolve the system path from typed system_path/model_ref parameters (XOR)."""
    return _get_system_path_arg({"system_path": system_path, "model_ref": model_ref})


def _system_paths_arg(
    system_paths: list[str] | None, model_refs: list[dict[str, Any]] | None
) -> list[str]:
    """Resolve system paths from typed system_paths/model_refs parameters (XOR)."""
    return _get_system_paths_arg({"system_paths": system_paths, "model_refs": model_refs})


def _get_system_paths_arg(args: dict[str, Any]) -> list[str]:
    """Extract list of system paths from system_paths or model_refs."""
    system_paths = args.get("system_paths")
    if isinstance(system_paths, list) and system_paths:
        return [str(path) for path in system_paths]

    model_refs = args.get("model_refs")
    if isinstance(model_refs, list) and model_refs:
        return [_resolve_model_ref_to_path(ref) for ref in model_refs if isinstance(ref, dict)]

    raise ValueError("Expected either 'system_paths' or 'model_refs'")


def _load_system_with_fallback_name(system_path: str) -> DistributionSystem:
    """Load a distribution system and ensure it has a non-empty name.

    Some cached models have null/blank top-level names, which can break MCP response
    schemas that require string fields. We normalize that case to the file stem so
    summary/diagnostics tools stay usable.
    """
    path = Path(system_path)
    system = DistributionSystem.from_json(system_path)

    if not isinstance(system.name, str) or not system.name.strip():
        system.name = path.stem

    return system


def _json_safe(value: Any) -> Any:
    """Coerce pandas/numpy/UUID/quantity values into JSON-serializable primitives."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Quantity):
        magnitude = value.magnitude
        return magnitude.tolist() if isinstance(magnitude, np.ndarray) else float(magnitude)
    if isinstance(value, (pd.Timestamp, pd.Timedelta)):
        return value.isoformat()
    if isinstance(value, timedelta):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    return value
