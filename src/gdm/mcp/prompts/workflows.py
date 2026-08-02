"""Pre-built prompt templates for common GDM workflows."""

from __future__ import annotations

from mcp.server import MCPServer


def register(mcp: MCPServer) -> None:
    """Register workflow prompt templates."""

    @mcp.prompt()
    def validate_and_fix(system_path: str) -> str:
        """Load a system, diagnose issues, suggest fixes, and apply them."""
        return f"""I'll help you validate and fix a distribution system.

1. First, call `diagnose_system` with the system path "{system_path}" to identify issues.
2. Review the diagnostics results.
3. Call `suggest_fixes` to get recommended fixes.
4. Call `apply_fixes` to apply the fixes.
5. Call `get_system_summary` to verify the results."""

    @mcp.prompt()
    def reduce_and_export(system_path: str, export_path: str) -> str:
        """Reduce a distribution system and export to GeoJSON."""
        return f"""I'll help you reduce a system and export it.

1. Call `get_system_summary` to inspect the system at "{system_path}".
2. Call `reduce_system` to reduce it.
3. Call `to_geojson` to export the reduced system to "{export_path}".
4. Call `save_system` to save the result."""

    @mcp.prompt()
    def analyze_system(system_path: str) -> str:
        """Load a system, get summary, analyze topology, and check time series."""
        return f"""I'll help you analyze a distribution system.

1. Call `get_system_summary` for an overview of "{system_path}".
2. Call `analyze_topology` to check the network structure.
3. Call `get_time_series_summary` to check time series data.
4. Call `get_component_relationships` to understand component connections."""
