"""System operations tools — merge, split, reduce, and save systems."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

from dist_stack.manifest import write_manifest
from dist_stack.registry import make_model_id, register as registry_register
from mcp.server import MCPServer

from gdm.distribution.model_reduction.reducer import (
    reduce_to_primary_system,
    reduce_to_three_phase_system,
)
from gdm.mcp import __version__
from gdm.mcp.common import _load_system_with_fallback_name, _system_path_arg, _system_paths_arg
from gdm.mcp.inspection import get_system_summary
from gdm.mcp.operations import merge_systems as _merge_systems_impl
from gdm.mcp.operations import split_by_feeder as _split_by_feeder_impl
from gdm.mcp.operations import split_by_substation as _split_by_substation_impl
from gdm.mcp.tools.control import _guard


def register(mcp: MCPServer) -> None:
    """Register the system operations tools."""

    @mcp.tool()
    @_guard
    async def merge_systems(
        system_paths: list[str] | None = None,
        model_refs: list[dict[str, Any]] | None = None,
        *,
        output_path: str,
        name: str,
        strict: bool = True,
    ) -> dict[str, Any]:
        """Merge multiple distribution systems into one. Preserves time series and detects conflicts.

        Args:
            system_paths: List of paths to distribution system JSON files to merge.
            model_refs: List of model reference objects for systems to merge.
            output_path: Path to save the merged system.
            name: Name for the merged system.
            strict: Error on conflicts (default: true).

        Returns:
            JSON payload with the merge report and output path.
        """
        paths = _system_paths_arg(system_paths, model_refs)
        systems = [_load_system_with_fallback_name(path) for path in paths]
        merged_system, report = _merge_systems_impl(systems, name, strict)

        # Save merged system
        merged_system.to_json(output_path, overwrite=True)

        return {
            "merge_report": report.model_dump(),
            "output_path": output_path,
        }

    @mcp.tool()
    @_guard
    async def split_by_substation(
        system_path: str | None = None,
        model_ref: dict[str, Any] | None = None,
        *,
        output_dir: str,
        keep_timeseries: bool = True,
        include_unassigned: bool = True,
    ) -> dict[str, Any]:
        """Split a distribution system into separate systems for each substation.

        Args:
            system_path: Path to the distribution system JSON file.
            model_ref: Model reference object with path or registry lookup metadata.
            output_dir: Directory to save the split systems.
            keep_timeseries: Preserve time series data (default: true).
            include_unassigned: Create system for unassigned components (default: true).

        Returns:
            JSON payload with the split report and output files.
        """
        path = _system_path_arg(system_path, model_ref)
        system = _load_system_with_fallback_name(path)
        subsystems, report = _split_by_substation_impl(system, keep_timeseries, include_unassigned)

        # Save subsystems
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        output_files = {}
        for sub_name, subsystem in subsystems.items():
            output_file = output_dir_path / f"{sub_name}.json"
            subsystem.to_json(str(output_file), overwrite=True)
            output_files[sub_name] = str(output_file)

        return {
            "split_report": report.model_dump(),
            "output_files": output_files,
        }

    @mcp.tool()
    @_guard
    async def split_by_feeder(
        system_path: str | None = None,
        model_ref: dict[str, Any] | None = None,
        *,
        output_dir: str,
        keep_timeseries: bool = True,
        include_unassigned: bool = True,
    ) -> dict[str, Any]:
        """Split a distribution system into separate systems for each feeder.

        Args:
            system_path: Path to the distribution system JSON file.
            model_ref: Model reference object with path or registry lookup metadata.
            output_dir: Directory to save the split systems.
            keep_timeseries: Preserve time series data (default: true).
            include_unassigned: Create system for unassigned components (default: true).

        Returns:
            JSON payload with the split report and output files.
        """
        path = _system_path_arg(system_path, model_ref)
        system = _load_system_with_fallback_name(path)
        subsystems, report = _split_by_feeder_impl(system, keep_timeseries, include_unassigned)

        # Save subsystems
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        output_files = {}
        for sub_name, subsystem in subsystems.items():
            output_file = output_dir_path / f"{sub_name}.json"
            subsystem.to_json(str(output_file), overwrite=True)
            output_files[sub_name] = str(output_file)

        return {
            "split_report": report.model_dump(),
            "output_files": output_files,
        }

    @mcp.tool()
    @_guard
    async def reduce_system(
        system_path: str | None = None,
        model_ref: dict[str, Any] | None = None,
        *,
        output_path: str,
        reducer: Literal["three_phase", "primary"] = "three_phase",
        name: str | None = None,
        keep_timeseries: bool = False,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Reduce a distribution system model (supports three-phase and primary reduction).

        Args:
            system_path: Path to the distribution system JSON file.
            model_ref: Model reference object with path or registry lookup metadata.
            output_path: Path to save the reduced system JSON file.
            reducer: Reducer type to apply.
            name: Optional name for reduced system.
            keep_timeseries: Include/aggregate time series in reduced system (default: false).
            overwrite: Overwrite output file if it exists (default: false).

        Returns:
            JSON payload with the output path and reduced system summary.
        """
        return await _reduce_system_impl(
            system_path=system_path,
            model_ref=model_ref,
            output_path=output_path,
            reducer=reducer,
            name=name,
            keep_timeseries=keep_timeseries,
            overwrite=overwrite,
        )

    @mcp.tool()
    @_guard
    async def save_system(
        system_path: str | None = None,
        model_ref: dict[str, Any] | None = None,
        *,
        output_path: str,
        name: str | None = None,
        overwrite: bool = False,
        model_id: str | None = None,
        version: int | None = None,
    ) -> dict[str, Any]:
        """Save a distribution system JSON to a target path using DistributionSystem.to_json.

        Args:
            system_path: Path to source distribution system JSON file.
            model_ref: Model reference object with path or registry lookup metadata.
            output_path: Path to write output distribution system JSON file.
            name: Optional system name override before saving.
            overwrite: Overwrite output file if it exists (default: false).
            model_id: Optional model registry id for the saved system.
            version: Optional model registry version for the saved system.

        Returns:
            JSON payload with the output path and saved system name.
        """
        return await _save_system_impl(
            system_path=system_path,
            model_ref=model_ref,
            output_path=output_path,
            name=name,
            overwrite=overwrite,
            model_id=model_id,
            version=version,
        )


async def _reduce_system_impl(
    system_path: str | None,
    model_ref: dict[str, Any] | None,
    output_path: str,
    reducer: str,
    name: str | None,
    keep_timeseries: bool,
    overwrite: bool,
) -> dict[str, Any]:
    """Reduce a distribution system model and save the result."""
    path = _system_path_arg(system_path, model_ref)
    output_file = Path(output_path)
    if output_file.exists() and not overwrite:
        raise ValueError(
            f"Output file already exists: {output_path}. Set overwrite=true to replace."
        )

    system = _load_system_with_fallback_name(path)
    reduced_name = name or f"{system.name}_reduced"

    reducer_func = {
        "three_phase": reduce_to_three_phase_system,
        "primary": reduce_to_primary_system,
    }
    if reducer not in reducer_func:
        raise ValueError(f"Unsupported reducer: {reducer}")

    reduced_system = reducer_func[reducer](system, reduced_name, keep_timeseries)
    reduced_system.to_json(output_path, overwrite=overwrite)

    summary = get_system_summary(reduced_system)
    return {
        "output_path": output_path,
        "reducer": reducer,
        "summary": summary.model_dump(),
    }


async def _save_system_impl(
    system_path: str | None,
    model_ref: dict[str, Any] | None,
    output_path: str,
    name: str | None,
    overwrite: bool,
    model_id: str | None,
    version: int | None,
) -> dict[str, Any]:
    """Save a distribution system JSON to a target path with provenance manifest."""
    path = _system_path_arg(system_path, model_ref)
    output_file = Path(output_path)
    if output_file.exists() and not overwrite:
        raise ValueError(
            f"Output file already exists: {output_path}. Set overwrite=true to replace."
        )

    system = _load_system_with_fallback_name(path)
    if name is not None:
        system.name = name

    system.to_json(output_path, overwrite=overwrite)
    result = {
        "output_path": output_path,
        "name": system.name,
    }
    record = None
    if os.getenv("DIST_STACK_MODEL_REGISTRY_DB"):
        record = registry_register(
            model_id=model_id or make_model_id(output_path),
            version=version,
            stored_path=output_path,
            metadata={
                "tool": "save_system",
                "tool_version": __version__,
                "package": "grid-data-models",
            },
        )
        result["model_id"] = record.model_id
        result["version"] = record.version
    write_manifest(
        output_path,
        artifact_type="gdm_system",
        tool="save_system",
        tool_version=__version__,
        package="grid-data-models",
        package_version=__version__,
        model_id=record.model_id if record is not None else None,
        model_version=record.version if record is not None else None,
        config={
            "data_format_version": (
                system.data_format_version if hasattr(system, "data_format_version") else None
            )
        },
    )
    return result
