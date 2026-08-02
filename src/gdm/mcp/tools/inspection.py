"""Inspection tools — summarize, query, and analyze distribution systems."""

from __future__ import annotations

from typing import Any, Literal

import pandas as pd
from mcp.server import MCPServer

from gdm.distribution import DistributionSystem
from gdm.mcp.common import _json_safe, _load_system_with_fallback_name, _system_path_arg
from gdm.mcp.inspection import (
    analyze_topology as _analyze_topology_impl,
)
from gdm.mcp.inspection import (
    find_orphaned_components as _find_orphaned_components_impl,
)
from gdm.mcp.inspection import (
    get_component_details as _get_component_details_impl,
)
from gdm.mcp.inspection import (
    get_component_relationships as _get_component_relationships_impl,
)
from gdm.mcp.inspection import get_system_summary as _get_system_summary_impl
from gdm.mcp.inspection import query_components as _query_components_impl
from gdm.mcp.inspection import validate_connectivity as _validate_connectivity_impl
from gdm.mcp.schemas import ComponentFilter
from gdm.mcp.tools.control import _guard
from gdm.mcp.utilities import get_time_series_summary as _get_time_series_summary_impl
from gdm.distribution.sys_functools import (
    get_aggregated_battery_time_series,
    get_combined_load_time_series_df,
    get_combined_solar_time_series_df,
)


def _battery_time_series_df(sys: DistributionSystem, var: str) -> pd.DataFrame:
    """Build a combined time series DataFrame for battery components."""
    from gdm.distribution.components import DistributionBattery

    batteries = list(sys.get_components(DistributionBattery))
    if not batteries:
        from gdm.exceptions import NoComponentsFoundError

        raise NoComponentsFoundError(f"No battery components found in {sys.name}.")
    ts = get_aggregated_battery_time_series(sys, batteries, var)
    timestamps = [ts.initial_timestamp + idx * ts.resolution for idx in range(ts.length)]
    data = ts.data.magnitude.tolist() if hasattr(ts.data, "magnitude") else list(ts.data)
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "name": [var] * ts.length,
            "component_uuid": ["aggregated_battery"] * ts.length,
            "value": data,
            "units": [str(ts.data.units)] * ts.length,
        }
    )


def register(mcp: MCPServer) -> None:
    """Register the inspection tools."""

    @mcp.tool()
    @_guard
    async def get_system_summary(
        system_path: str | None = None,
        model_ref: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get comprehensive summary of a distribution system including component counts, substations, feeders, and time series.

        Args:
            system_path: Path to the distribution system JSON file.
            model_ref: Model reference object with path or registry lookup metadata.

        Returns:
            JSON payload with the system summary.
        """
        path = _system_path_arg(system_path, model_ref)
        system = _load_system_with_fallback_name(path)
        summary = _get_system_summary_impl(system)
        return summary.model_dump()

    @mcp.tool()
    @_guard
    async def query_components(
        system_path: str | None = None,
        model_ref: dict[str, Any] | None = None,
        component_types: list[str] | None = None,
        substation: str | None = None,
        feeder: str | None = None,
        phases: list[str] | None = None,
        in_service: bool | None = None,
        has_timeseries: bool | None = None,
    ) -> dict[str, Any]:
        """Query and filter components in a distribution system by type, substation, feeder, phases, etc.

        Args:
            system_path: Path to the distribution system JSON file.
            model_ref: Model reference object with path or registry lookup metadata.
            component_types: Filter by component types (optional).
            substation: Filter by substation name (optional).
            feeder: Filter by feeder name (optional).
            phases: Filter by phases (optional).
            in_service: Filter by in_service status (optional).
            has_timeseries: Filter by time series presence (optional).

        Returns:
            JSON payload with the matching components.
        """
        path = _system_path_arg(system_path, model_ref)
        system = _load_system_with_fallback_name(path)

        filters = ComponentFilter(
            component_types=component_types,
            substation=substation,
            feeder=feeder,
            phases=phases,
            in_service=in_service,
            has_timeseries=has_timeseries,
        )

        components = _query_components_impl(system, filters)
        return {"components": [c.model_dump() for c in components], "count": len(components)}

    @mcp.tool()
    @_guard
    async def analyze_topology(
        system_path: str | None = None,
        model_ref: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Analyze network topology: node/edge counts, cycles, islands, radial check, source bus.

        Args:
            system_path: Path to the distribution system JSON file.
            model_ref: Model reference object with path or registry lookup metadata.

        Returns:
            JSON payload with the topology metrics.
        """
        path = _system_path_arg(system_path, model_ref)
        system = _load_system_with_fallback_name(path)
        metrics = _analyze_topology_impl(system)
        return metrics.model_dump()

    @mcp.tool()
    @_guard
    async def validate_connectivity(
        system_path: str | None = None,
        model_ref: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Validate that all buses are reachable from the source bus. Identifies islands and unreachable components.

        Args:
            system_path: Path to the distribution system JSON file.
            model_ref: Model reference object with path or registry lookup metadata.

        Returns:
            JSON payload with the connectivity validation result.
        """
        path = _system_path_arg(system_path, model_ref)
        system = _load_system_with_fallback_name(path)
        return _validate_connectivity_impl(system)

    @mcp.tool()
    @_guard
    async def get_component_details(
        system_path: str | None = None,
        model_ref: dict[str, Any] | None = None,
        *,
        identifier: str,
    ) -> dict[str, Any]:
        """Get detailed information about a specific component by UUID or name.

        Args:
            system_path: Path to the distribution system JSON file.
            model_ref: Model reference object with path or registry lookup metadata.
            identifier: Component UUID or name.

        Returns:
            JSON payload with the component details.
        """
        path = _system_path_arg(system_path, model_ref)
        system = _load_system_with_fallback_name(path)
        return _get_component_details_impl(system, identifier)

    @mcp.tool()
    @_guard
    async def find_orphaned_components(
        system_path: str | None = None,
        model_ref: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Find components without substation or feeder assignments.

        Args:
            system_path: Path to the distribution system JSON file.
            model_ref: Model reference object with path or registry lookup metadata.

        Returns:
            JSON payload with the orphaned components.
        """
        path = _system_path_arg(system_path, model_ref)
        system = _load_system_with_fallback_name(path)
        orphaned = _find_orphaned_components_impl(system)
        return {"orphaned_components": [c.model_dump() for c in orphaned], "count": len(orphaned)}

    @mcp.tool()
    @_guard
    async def get_component_relationships(
        system_path: str | None = None,
        model_ref: dict[str, Any] | None = None,
        *,
        component_id: str,
    ) -> dict[str, Any]:
        """Get parent and child relationships for a component.

        Args:
            system_path: Path to the distribution system JSON file.
            model_ref: Model reference object with path or registry lookup metadata.
            component_id: Component UUID or name.

        Returns:
            JSON payload with the parent and child components.
        """
        path = _system_path_arg(system_path, model_ref)
        system = _load_system_with_fallback_name(path)
        relationships = _get_component_relationships_impl(system, component_id)
        return {
            "parents": [p.model_dump() for p in relationships.get("parents", [])],
            "children": [c.model_dump() for c in relationships.get("children", [])],
        }

    @mcp.tool()
    @_guard
    async def get_time_series_summary(
        system_path: str | None = None,
        model_ref: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get summary of all time series data in the system.

        Args:
            system_path: Path to the distribution system JSON file.
            model_ref: Model reference object with path or registry lookup metadata.

        Returns:
            JSON payload with the time series summary.
        """
        path = _system_path_arg(system_path, model_ref)
        system = _load_system_with_fallback_name(path)
        return _get_time_series_summary_impl(system)

    @mcp.tool()
    @_guard
    async def get_time_series_values(
        system_path: str,
        component_type: Literal["load", "solar", "battery", "all"] = "all",
        var_of_interest: str = "active_power",
    ) -> dict[str, Any]:
        """Get combined time series data for load, solar, or battery components as rows of timestamp/value pairs.

        Args:
            system_path: Path to the distribution system JSON file.
            component_type: Component type to aggregate (default: all).
            var_of_interest: Time series variable to return (e.g., 'active_power'). Solar time series are stored as 'irradiance' and mapped to 'active_power' in the returned rows (default: active_power).

        Returns:
            JSON payload with the combined time series rows.
        """
        return await _get_time_series_values_impl(system_path, component_type, var_of_interest)


async def _get_time_series_values_impl(
    system_path: str,
    component_type: str,
    var_of_interest: str,
) -> dict[str, Any]:
    """Get combined time series values for load, solar, battery, or all components."""
    system = _load_system_with_fallback_name(system_path)

    if component_type == "load":
        df = get_combined_load_time_series_df(
            system, unit_conversion={}, var_of_interest={var_of_interest}
        )
    elif component_type == "solar":
        # Solar time series are stored under 'irradiance' and renamed to 'active_power' by the library.
        solar_var = var_of_interest if var_of_interest == "irradiance" else "irradiance"
        df = get_combined_solar_time_series_df(
            system, unit_conversion={}, var_of_interest={solar_var}
        )
    elif component_type == "battery":
        df = _battery_time_series_df(system, var_of_interest)
    elif component_type == "all":
        load_var = var_of_interest
        solar_var = var_of_interest if var_of_interest == "irradiance" else "irradiance"
        load_df = get_combined_load_time_series_df(
            system, unit_conversion={}, var_of_interest={load_var}
        )
        solar_df = get_combined_solar_time_series_df(
            system, unit_conversion={}, var_of_interest={solar_var}
        )
        df = pd.concat([load_df, solar_df], ignore_index=True)
    else:
        msg = (
            f"Unsupported component_type: {component_type}. "
            f"Expected one of: load, solar, battery, all"
        )
        raise ValueError(msg)

    rows = [
        {key: _json_safe(value) for key, value in record.items()}
        for record in df.to_dict(orient="records")
    ]
    return {
        "component_type": component_type,
        "var_of_interest": var_of_interest,
        "columns": list(df.columns),
        "rows": rows,
        "count": len(rows),
    }
