"""MCP Server for Grid Data Models.

This module provides the main MCP server implementation that exposes
grid-data-models functionality as tools for AI agents.
"""

from __future__ import annotations

import logging
from typing import Annotated

import typer
from mcp.server import MCPServer

from gdm.mcp import __version__

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gdm_mcp")


def create_server() -> MCPServer:
    """Create and configure the MCPServer server instance."""
    mcp = MCPServer(
        "grid-data-models-mcp",
        version=__version__,
        instructions=(
            "Grid Data Models MCP server for creating, validating, inspecting, and "
            "analyzing power distribution system models. Use the tools to diagnose "
            "and fix validation issues, merge or split feeders, reduce models, "
            "export GeoJSON and plots, inspect topology and time series, and query "
            "the GDM documentation."
        ),
    )

    # -- Register tool modules -------------------------------------------------
    from gdm.mcp.tools import (
        control,
        export,
        inspection,
        knowledge,
        operations,
        tracked_changes,
        validation,
    )

    validation.register(mcp)
    operations.register(mcp)
    inspection.register(mcp)
    export.register(mcp)
    tracked_changes.register(mcp)
    knowledge.register(mcp)
    control.register(mcp)

    # -- Register resources ----------------------------------------------------
    from gdm.mcp.resources import index as index_resources

    index_resources.register(mcp)

    # -- Register prompts ------------------------------------------------------
    from gdm.mcp.prompts import workflows

    workflows.register(mcp)

    return mcp


def _run_server(
    log_level: Annotated[str, typer.Option(help="Logging level")] = "INFO",
    tool_calls_enabled: Annotated[
        bool,
        typer.Option(
            "--tool-calls-enabled/--tool-calls-disabled",
            help="Start server with non-control tool calls enabled or disabled.",
        ),
    ] = True,
):
    """Start the GDM MCP server."""
    # Set log level
    logging.getLogger("gdm_mcp").setLevel(log_level.upper())

    logger.info(f"Starting GDM MCP Server v{__version__}")
    logger.info(f"Tool calls enabled: {tool_calls_enabled}")

    import gdm.mcp.tools.control as control

    control._TOOL_CALLS_ENABLED = tool_calls_enabled

    # Run the server
    create_server().run(transport="stdio")


def main():
    typer.run(_run_server)


if __name__ == "__main__":
    main()
