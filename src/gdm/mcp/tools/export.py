"""Export tools — subsystem extraction, GeoJSON export, and plotting."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from mcp.server import MCPServer

from gdm.distribution.enums import ColorLineBy, ColorNodeBy, MapType
from gdm.mcp.common import _load_system_with_fallback_name, _system_path_arg
from gdm.mcp.inspection import get_system_summary
from gdm.mcp.tools.control import _guard
from gdm.mcp.utilities import export_subsystem_by_buses as _export_subsystem_by_buses_impl


def register(mcp: MCPServer) -> None:
    """Register the export tools."""

    @mcp.tool()
    @_guard
    async def export_subsystem_by_buses(
        system_path: str | None = None,
        model_ref: dict[str, Any] | None = None,
        *,
        bus_names: list[str],
        output_path: str,
        name: str,
        keep_timeseries: bool = True,
    ) -> dict[str, Any]:
        """Extract a subsystem containing specified buses and their connected components.

        Args:
            system_path: Path to the distribution system JSON file.
            model_ref: Model reference object with path or registry lookup metadata.
            bus_names: List of bus names to include.
            output_path: Path to save the subsystem.
            name: Name for the subsystem.
            keep_timeseries: Preserve time series (default: true).

        Returns:
            JSON payload with the output path and subsystem summary.
        """
        path = _system_path_arg(system_path, model_ref)
        system = _load_system_with_fallback_name(path)
        subsystem = _export_subsystem_by_buses_impl(system, bus_names, name, keep_timeseries)

        # Save subsystem
        subsystem.to_json(output_path, overwrite=True)

        summary = get_system_summary(subsystem)
        return {
            "output_path": output_path,
            "subsystem_summary": summary.model_dump(),
        }

    @mcp.tool()
    @_guard
    async def to_geojson(system_path: str, export_file: str) -> dict[str, Any]:
        """Export the distribution system to a GeoJSON file.

        Args:
            system_path: Path to the distribution system JSON file.
            export_file: Path to the output GeoJSON file.

        Returns:
            JSON payload with the output path.
        """
        system = _load_system_with_fallback_name(system_path)
        system.to_geojson(export_file)

        return {"output_path": str(export_file), "message": f"GeoJSON exported to {export_file}"}

    @mcp.tool()
    @_guard
    async def plot_system(
        system_path: str,
        export_path: str | None = None,
        show: bool = False,
        color_node_by: Literal["phase", "voltage", "equipment_type"] = "phase",
        color_line_by: Literal["phase", "equipment_type"] = "equipment_type",
        map_type: Literal["scatter_geo", "scatter_mapbox"] = "scatter_geo",
    ) -> dict[str, Any]:
        """Generate an interactive HTML plot of the distribution system and optionally export it to a directory.

        Args:
            system_path: Path to the distribution system JSON file.
            export_path: Directory to save the plot HTML file (created if missing).
            show: Open the plot in a browser (default: false).
            color_node_by: Attribute used to color nodes (default: phase).
            color_line_by: Attribute used to color lines (default: equipment_type).
            map_type: Map type for the plot (default: scatter_geo).

        Returns:
            JSON payload with the plot output path.
        """
        system = _load_system_with_fallback_name(system_path)

        color_node_map = {
            "phase": ColorNodeBy.PHASE,
            "voltage": ColorNodeBy.VOLTAGE_LEVEL,
            "equipment_type": ColorNodeBy.EQUIPMENT_TYPE,
        }
        color_line_map = {
            "phase": ColorLineBy.PHASE,
            "equipment_type": ColorLineBy.EQUIPMENT_TYPE,
        }
        map_type_map = {
            "scatter_geo": MapType.SCATTER_GEO,
            "scatter_mapbox": MapType.SCATTER_MAP,
        }

        plot_dir = Path(export_path) if export_path else None
        plot_file = None
        if plot_dir is not None:
            plot_dir.mkdir(parents=True, exist_ok=True)
            plot_file = plot_dir / f"{system.name}_plot.html"

        system.plot(
            export_path=plot_dir,
            show=show,
            color_node_by=color_node_map[color_node_by],
            color_line_by=color_line_map[color_line_by],
            map_type=map_type_map[map_type],
        )

        if plot_file is not None:
            message = f"Plot exported to {plot_file}"
        else:
            message = "Plot generated; no export_path provided, so it was not saved to disk."
        return {"output_path": str(plot_file) if plot_file else None, "message": message}
