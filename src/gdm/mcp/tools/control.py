"""Control tools — runtime toggle for serving non-control tool calls."""

from __future__ import annotations

import asyncio
import functools
from typing import Any

from mcp.server import MCPServer

# Runtime toggle for serving tool calls. Control tools remain available.
_TOOL_CALLS_ENABLED = True

_DISABLED_PAYLOAD = {
    "error": "Tool calls are currently disabled. Use set_tool_calls_enabled to re-enable."
}


def _guard(func):
    """Wrap a non-control tool so it returns the disabled-error payload while disabled."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if not _TOOL_CALLS_ENABLED:
            return _DISABLED_PAYLOAD
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)

    return wrapper


def register(mcp: MCPServer) -> None:
    """Register the control tools."""

    @mcp.tool()
    async def set_tool_calls_enabled(enabled: bool) -> dict[str, Any]:
        """Enable or disable non-control MCP tool calls at runtime.

        Args:
            enabled: Whether normal tool calls should be enabled.

        Returns:
            JSON payload with the new runtime state.
        """
        global _TOOL_CALLS_ENABLED

        _TOOL_CALLS_ENABLED = bool(enabled)
        return {
            "tool_calls_enabled": _TOOL_CALLS_ENABLED,
            "message": (
                "Non-control tool calls are enabled"
                if _TOOL_CALLS_ENABLED
                else "Non-control tool calls are disabled"
            ),
        }

    @mcp.tool()
    async def get_tool_calls_enabled() -> dict[str, Any]:
        """Get current runtime state for MCP tool-call enablement.

        Returns:
            JSON payload with the current runtime toggle state.
        """
        return {"tool_calls_enabled": _TOOL_CALLS_ENABLED}
