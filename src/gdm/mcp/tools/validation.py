"""Validation tools — diagnose, suggest fixes for, and apply fixes to systems."""

from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from gdm.mcp.common import _load_system_with_fallback_name, _system_path_arg
from gdm.mcp.tools.control import _guard
from gdm.mcp.validation import apply_fixes as _apply_fixes_impl
from gdm.mcp.validation import diagnose_system as _diagnose_system_impl
from gdm.mcp.validation import suggest_fixes as _suggest_fixes_impl


def register(mcp: MCPServer) -> None:
    """Register the validation tools."""

    @mcp.tool()
    @_guard
    async def diagnose_system(
        system_path: str | None = None,
        model_ref: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Diagnose validation errors in a distribution system. Returns detailed error report with component UUIDs, error types, and affected fields.

        Args:
            system_path: Path to the distribution system JSON file.
            model_ref: Model reference object with path or registry lookup metadata.

        Returns:
            JSON payload with the validation report.
        """
        path = _system_path_arg(system_path, model_ref)
        system = _load_system_with_fallback_name(path)
        report = _diagnose_system_impl(system)
        return report.model_dump()

    @mcp.tool()
    @_guard
    async def suggest_fixes(
        system_path: str | None = None,
        model_ref: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate fix suggestions for validation errors. Analyzes error report and proposes strategies with confidence levels.

        Args:
            system_path: Path to the distribution system JSON file.
            model_ref: Model reference object with path or registry lookup metadata.

        Returns:
            JSON payload with the validation report and fix suggestions.
        """
        path = _system_path_arg(system_path, model_ref)
        system = _load_system_with_fallback_name(path)
        report = _diagnose_system_impl(system)
        suggestions = _suggest_fixes_impl(report)
        return {
            "validation_report": report.model_dump(),
            "suggestions": [s.model_dump() for s in suggestions],
        }

    @mcp.tool()
    @_guard
    async def apply_fixes(
        system_path: str | None = None,
        model_ref: dict[str, Any] | None = None,
        *,
        output_path: str,
        auto_approve: bool = False,
    ) -> dict[str, Any]:
        """Automatically apply fixes to a distribution system. Creates a fixed copy and returns change log.

        Args:
            system_path: Path to the distribution system JSON file.
            model_ref: Model reference object with path or registry lookup metadata.
            output_path: Path to save the fixed system.
            auto_approve: Whether to apply low-confidence fixes (default: false).

        Returns:
            JSON payload with the fix result and output path.
        """
        path = _system_path_arg(system_path, model_ref)
        system = _load_system_with_fallback_name(path)
        report = _diagnose_system_impl(system)
        suggestions = _suggest_fixes_impl(report)

        fixed_system, fix_result = _apply_fixes_impl(system, suggestions, auto_approve)

        # Save fixed system
        fixed_system.to_json(output_path, overwrite=True)

        return {
            "fix_result": fix_result.model_dump(),
            "output_path": output_path,
        }
