"""Tracked changes tools — apply tracked changes to a distribution system."""

from __future__ import annotations

import os
import tempfile
from typing import Any

from mcp.server import MCPServer

from gdm.distribution import DistributionSystem
from gdm.mcp.common import _load_system_with_fallback_name
from gdm.mcp.tools.control import _guard
from gdm.tracked_changes import (
    TrackedChange,
    apply_updates_to_system,
    filter_tracked_changes_by_name_and_date,
)


def _load_tracked_changes(tracked_changes_path: str) -> list[TrackedChange]:
    """Load TrackedChange objects from a JSON file containing a system of tracked changes."""
    container = DistributionSystem.from_json(tracked_changes_path)
    return list(container.get_components(TrackedChange))


def _save_tracked_changes(tracked_changes: list[TrackedChange], output_path: str) -> str:
    """Serialize TrackedChange objects to a JSON file containing a system of tracked changes."""
    container = DistributionSystem(name="tracked_changes", auto_add_composed_components=True)
    for change in tracked_changes:
        container.add_component(change)
    container.to_json(output_path, overwrite=True)
    return output_path


def register(mcp: MCPServer) -> None:
    """Register the tracked changes tools."""

    @mcp.tool()
    @_guard
    async def apply_tracked_changes(
        system_path: str,
        tracked_changes_path: str,
        scenario_name: str | None = None,
        output_path: str | None = None,
    ) -> dict[str, Any]:
        """Apply tracked changes (additions, edits, deletions) to a distribution system and save the updated system.

        Args:
            system_path: Path to the distribution system JSON file.
            tracked_changes_path: Path to a JSON file containing a list of TrackedChange objects.
            scenario_name: Only apply changes belonging to this scenario (optional).
            output_path: Path to save the updated system (default: temporary file).

        Returns:
            JSON payload with the output path and number of changes applied.
        """
        system = _load_system_with_fallback_name(system_path)
        tracked_changes = _load_tracked_changes(tracked_changes_path)

        if scenario_name:
            tracked_changes = filter_tracked_changes_by_name_and_date(
                tracked_changes, scenario_name=scenario_name
            )

        if not tracked_changes:
            raise ValueError("No tracked changes to apply after filtering.")

        updated_system = apply_updates_to_system(tracked_changes, system, catalog=None)

        if not output_path:
            fd, tmp_file = tempfile.mkstemp(prefix="gdm_tracked_changes_", suffix=".json")
            os.close(fd)
            output_path = tmp_file

        updated_system.to_json(output_path, overwrite=True)

        return {
            "output_path": output_path,
            "scenario_name": scenario_name,
            "changes_applied": len(tracked_changes),
        }
