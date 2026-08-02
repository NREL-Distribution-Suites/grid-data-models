"""Canonical index resources — components, tools, and workflows."""

from __future__ import annotations

import json

from mcp.server import MCPServer

from gdm.mcp.knowledge.documentation import list_available_components


def register(mcp: MCPServer) -> None:
    """Register the canonical index resources."""

    @mcp.resource("gdm://components", name="Available Components", mime_type="application/json")
    async def components() -> str:
        """All registered distribution component types."""
        components = list_available_components()
        return json.dumps([component.model_dump() for component in components], indent=2)

    @mcp.resource("gdm://tools", name="Available Tools", mime_type="application/json")
    async def tools() -> str:
        """All registered MCP tools with descriptions."""
        tool_list = await mcp.list_tools()
        data = [{"name": tool.name, "description": tool.description} for tool in tool_list]
        return json.dumps(data, indent=2)

    @mcp.resource("gdm://workflows", name="Canonical Workflows", mime_type="application/json")
    async def workflows() -> str:
        """Pre-defined workflow prompts for common tasks."""
        prompt_list = await mcp.list_prompts()
        data = [{"name": prompt.name, "description": prompt.description} for prompt in prompt_list]
        return json.dumps(data, indent=2)
