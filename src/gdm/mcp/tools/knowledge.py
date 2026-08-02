"""Knowledge tools — search documentation and inspect GDM component APIs."""

from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from gdm.mcp.knowledge.documentation import (
    get_api_reference as _get_api_reference_impl,
)
from gdm.mcp.knowledge.documentation import (
    get_code_examples as _get_code_examples_impl,
)
from gdm.mcp.knowledge.documentation import (
    get_component_fields as _get_component_fields_impl,
)
from gdm.mcp.knowledge.documentation import (
    list_available_components as _list_available_components_impl,
)
from gdm.mcp.knowledge.documentation import (
    search_documentation as _search_documentation_impl,
)
from gdm.mcp.tools.control import _guard


def register(mcp: MCPServer) -> None:
    """Register the knowledge tools."""

    @mcp.tool()
    @_guard
    async def search_gdm_documentation(query: str, max_results: int = 5) -> dict[str, Any]:
        """Search grid-data-models documentation for relevant content. Returns snippets from docs, API references, and notebooks.

        Args:
            query: Search query (e.g., 'how to create a bus', 'time series', 'phase').
            max_results: Maximum number of results to return (default: 5).

        Returns:
            JSON payload with the search results.
        """
        results = _search_documentation_impl(query, max_results)
        return {"query": query, "results": [r.model_dump() for r in results]}

    @mcp.tool()
    @_guard
    async def get_api_reference(component_name: str) -> dict[str, Any]:
        """Get detailed API reference for a specific component class (e.g., DistributionBus, DistributionLoad). Returns fields, methods, and usage examples.

        Args:
            component_name: Name of the component class (e.g., 'DistributionBus').

        Returns:
            JSON payload with the API reference.
        """
        result = _get_api_reference_impl(component_name)
        return result.model_dump()

    @mcp.tool()
    @_guard
    async def get_code_examples(topic: str) -> dict[str, Any]:
        """Get code examples for a specific topic from documentation notebooks.

        Args:
            topic: Topic to search for (e.g., 'creating a bus', 'time series', 'plotting').

        Returns:
            JSON payload with the code examples.
        """
        examples = _get_code_examples_impl(topic)
        return {"topic": topic, "examples": [e.model_dump() for e in examples]}

    @mcp.tool()
    @_guard
    async def list_available_components() -> dict[str, Any]:
        """List all available distribution component types with descriptions.

        Returns:
            JSON payload with the available component types.
        """
        components = _list_available_components_impl()
        return {"components": [c.model_dump() for c in components]}

    @mcp.tool()
    @_guard
    async def get_component_fields(component_name: str) -> dict[str, Any]:
        """Get detailed field information for a specific component type, including types, requirements, and defaults.

        Args:
            component_name: Name of the component class (e.g., 'DistributionBus').

        Returns:
            JSON payload with the component fields.
        """
        fields = _get_component_fields_impl(component_name)
        return {"component_name": component_name, "fields": fields}
