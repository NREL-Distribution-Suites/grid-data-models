"""MCP Server for Grid Data Models.

This module provides the main MCP server implementation that exposes
grid-data-models functionality as tools for AI agents.
"""

import json
import logging
import os
import tempfile
from datetime import timedelta
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID

import numpy as np
import pandas as pd
import typer
from dist_stack.manifest import write_manifest
from dist_stack.registry import register, make_model_id, resolve_model_ref
from gdm.distribution import DistributionSystem
from mcp.server import Server, ServerRequestContext
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    GetPromptResult,
    ListPromptsResult,
    ListResourcesResult,
    ListToolsResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    ReadResourceResult,
    Resource,
    TextContent,
    TextResourceContents,
    Tool,
)
from pint import Quantity

from gdm.mcp import __version__
from gdm.mcp.exceptions import GDMMCPException
from gdm.mcp.inspection import (
    analyze_topology,
    find_orphaned_components,
    get_component_details,
    get_component_relationships,
    get_system_summary,
    query_components,
    validate_connectivity,
)
from gdm.mcp.operations import merge_systems, split_by_feeder, split_by_substation
from gdm.mcp.schemas import ComponentFilter
from gdm.mcp.utilities import (
    export_subsystem_by_buses,
    get_time_series_summary,
)
from gdm.mcp.validation import apply_fixes, diagnose_system, suggest_fixes
from gdm.mcp.knowledge.documentation import (
    search_documentation,
    get_api_reference as get_api_ref,
    get_code_examples as get_code_ex,
    list_available_components as list_components_doc,
    get_component_fields as get_fields_doc,
)
from gdm.distribution.model_reduction.reducer import (
    reduce_to_primary_system,
    reduce_to_three_phase_system,
)
from gdm.distribution.enums import ColorLineBy, ColorNodeBy, MapType
from gdm.distribution.sys_functools import (
    get_aggregated_battery_time_series,
    get_combined_load_time_series_df,
    get_combined_solar_time_series_df,
)
from gdm.tracked_changes import (
    TrackedChange,
    apply_updates_to_system,
    filter_tracked_changes_by_name_and_date,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gdm_mcp")

# Runtime toggle for serving tool calls. Control tools remain available.
_TOOL_CALLS_ENABLED = True
_CONTROL_TOOLS = {"set_tool_calls_enabled", "get_tool_calls_enabled"}


def _load_system_with_fallback_name(system_path: str) -> DistributionSystem:
    """Load a distribution system and ensure it has a non-empty name.

    Some cached models have null/blank top-level names, which can break MCP response
    schemas that require string fields. We normalize that case to the file stem so
    summary/diagnostics tools stay usable.
    """
    path = Path(system_path)
    system = DistributionSystem.from_json(system_path)

    if not isinstance(system.name, str) or not system.name.strip():
        system.name = path.stem

    return system


def _resolve_model_ref_to_path(model_ref: dict[str, Any]) -> str:
    """Resolve a model_ref payload to a concrete system JSON path.

    Path-carrying refs pass through; model_id/version resolve via the
    dist_stack model registry (DIST_STACK_MODEL_REGISTRY_DB).
    """
    return resolve_model_ref(model_ref)


def _get_system_path_arg(args: dict[str, Any]) -> str:
    """Extract system path from legacy system_path or model_ref input."""
    if isinstance(args.get("system_path"), str) and args["system_path"].strip():
        return str(args["system_path"])

    model_ref = args.get("model_ref")
    if isinstance(model_ref, dict):
        return _resolve_model_ref_to_path(model_ref)

    raise ValueError("Expected either 'system_path' or 'model_ref'")


def _get_system_paths_arg(args: dict[str, Any]) -> list[str]:
    """Extract list of system paths from system_paths or model_refs."""
    system_paths = args.get("system_paths")
    if isinstance(system_paths, list) and system_paths:
        return [str(path) for path in system_paths]

    model_refs = args.get("model_refs")
    if isinstance(model_refs, list) and model_refs:
        return [_resolve_model_ref_to_path(ref) for ref in model_refs if isinstance(ref, dict)]

    raise ValueError("Expected either 'system_paths' or 'model_refs'")


def _split_tool_input_schema() -> dict[str, Any]:
    """Build shared input schema for split tools."""
    return {
        "type": "object",
        "properties": {
            "system_path": {
                "type": "string",
                "description": "Path to the distribution system JSON file",
            },
            "model_ref": {
                "type": "object",
                "description": "Model reference object with path or registry lookup metadata",
            },
            "output_dir": {
                "type": "string",
                "description": "Directory to save the split systems",
            },
            "keep_timeseries": {
                "type": "boolean",
                "description": "Preserve time series data (default: true)",
                "default": True,
            },
            "include_unassigned": {
                "type": "boolean",
                "description": "Create system for unassigned components (default: true)",
                "default": True,
            },
        },
        "required": ["output_dir"],
        "anyOf": [{"required": ["system_path"]}, {"required": ["model_ref"]}],
    }


async def list_tools(ctx: ServerRequestContext, params=None) -> ListToolsResult:
    """List all available MCP tools."""
    tools = [
        # Validation tools
        Tool(
            name="diagnose_system",
            description="Diagnose validation errors in a distribution system. Returns detailed error report with component UUIDs, error types, and affected fields.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_path": {
                        "type": "string",
                        "description": "Path to the distribution system JSON file",
                    },
                    "model_ref": {
                        "type": "object",
                        "description": "Model reference object with path or registry lookup metadata",
                    },
                },
                "anyOf": [{"required": ["system_path"]}, {"required": ["model_ref"]}],
            },
        ),
        Tool(
            name="suggest_fixes",
            description="Generate fix suggestions for validation errors. Analyzes error report and proposes strategies with confidence levels.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_path": {
                        "type": "string",
                        "description": "Path to the distribution system JSON file",
                    },
                    "model_ref": {
                        "type": "object",
                        "description": "Model reference object with path or registry lookup metadata",
                    },
                },
                "anyOf": [{"required": ["system_path"]}, {"required": ["model_ref"]}],
            },
        ),
        Tool(
            name="apply_fixes",
            description="Automatically apply fixes to a distribution system. Creates a fixed copy and returns change log.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_path": {
                        "type": "string",
                        "description": "Path to the distribution system JSON file",
                    },
                    "model_ref": {
                        "type": "object",
                        "description": "Model reference object with path or registry lookup metadata",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path to save the fixed system",
                    },
                    "auto_approve": {
                        "type": "boolean",
                        "description": "Whether to apply low-confidence fixes (default: false)",
                        "default": False,
                    },
                },
                "required": ["output_path"],
                "anyOf": [{"required": ["system_path"]}, {"required": ["model_ref"]}],
            },
        ),
        # System operation tools
        Tool(
            name="merge_systems",
            description="Merge multiple distribution systems into one. Preserves time series and detects conflicts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of paths to distribution system JSON files to merge",
                    },
                    "model_refs": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of model reference objects for systems to merge",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path to save the merged system",
                    },
                    "name": {
                        "type": "string",
                        "description": "Name for the merged system",
                    },
                    "strict": {
                        "type": "boolean",
                        "description": "Error on conflicts (default: true)",
                        "default": True,
                    },
                },
                "required": ["output_path", "name"],
                "anyOf": [{"required": ["system_paths"]}, {"required": ["model_refs"]}],
            },
        ),
        Tool(
            name="split_by_substation",
            description="Split a distribution system into separate systems for each substation.",
            inputSchema=_split_tool_input_schema(),
        ),
        Tool(
            name="split_by_feeder",
            description="Split a distribution system into separate systems for each feeder.",
            inputSchema=_split_tool_input_schema(),
        ),
        Tool(
            name="reduce_system",
            description="Reduce a distribution system model (supports three-phase and primary reduction).",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_path": {
                        "type": "string",
                        "description": "Path to the distribution system JSON file",
                    },
                    "model_ref": {
                        "type": "object",
                        "description": "Model reference object with path or registry lookup metadata",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path to save the reduced system JSON file",
                    },
                    "reducer": {
                        "type": "string",
                        "description": "Reducer type to apply",
                        "enum": ["three_phase", "primary"],
                        "default": "three_phase",
                    },
                    "name": {
                        "type": "string",
                        "description": "Optional name for reduced system",
                    },
                    "keep_timeseries": {
                        "type": "boolean",
                        "description": "Include/aggregate time series in reduced system (default: false)",
                        "default": False,
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": "Overwrite output file if it exists (default: false)",
                        "default": False,
                    },
                },
                "required": ["output_path"],
                "anyOf": [{"required": ["system_path"]}, {"required": ["model_ref"]}],
            },
        ),
        # Inspection tools
        Tool(
            name="get_system_summary",
            description="Get comprehensive summary of a distribution system including component counts, substations, feeders, and time series.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_path": {
                        "type": "string",
                        "description": "Path to the distribution system JSON file",
                    },
                    "model_ref": {
                        "type": "object",
                        "description": "Model reference object with path or registry lookup metadata",
                    },
                },
                "anyOf": [{"required": ["system_path"]}, {"required": ["model_ref"]}],
            },
        ),
        Tool(
            name="query_components",
            description="Query and filter components in a distribution system by type, substation, feeder, phases, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_path": {
                        "type": "string",
                        "description": "Path to the distribution system JSON file",
                    },
                    "model_ref": {
                        "type": "object",
                        "description": "Model reference object with path or registry lookup metadata",
                    },
                    "component_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by component types (optional)",
                    },
                    "substation": {
                        "type": "string",
                        "description": "Filter by substation name (optional)",
                    },
                    "feeder": {
                        "type": "string",
                        "description": "Filter by feeder name (optional)",
                    },
                    "phases": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by phases (optional)",
                    },
                    "in_service": {
                        "type": "boolean",
                        "description": "Filter by in_service status (optional)",
                    },
                    "has_timeseries": {
                        "type": "boolean",
                        "description": "Filter by time series presence (optional)",
                    },
                },
                "anyOf": [{"required": ["system_path"]}, {"required": ["model_ref"]}],
            },
        ),
        Tool(
            name="analyze_topology",
            description="Analyze network topology: node/edge counts, cycles, islands, radial check, source bus.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_path": {
                        "type": "string",
                        "description": "Path to the distribution system JSON file",
                    },
                    "model_ref": {
                        "type": "object",
                        "description": "Model reference object with path or registry lookup metadata",
                    },
                },
                "anyOf": [{"required": ["system_path"]}, {"required": ["model_ref"]}],
            },
        ),
        Tool(
            name="validate_connectivity",
            description="Validate that all buses are reachable from the source bus. Identifies islands and unreachable components.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_path": {
                        "type": "string",
                        "description": "Path to the distribution system JSON file",
                    },
                    "model_ref": {
                        "type": "object",
                        "description": "Model reference object with path or registry lookup metadata",
                    },
                },
                "anyOf": [{"required": ["system_path"]}, {"required": ["model_ref"]}],
            },
        ),
        Tool(
            name="get_component_details",
            description="Get detailed information about a specific component by UUID or name.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_path": {
                        "type": "string",
                        "description": "Path to the distribution system JSON file",
                    },
                    "model_ref": {
                        "type": "object",
                        "description": "Model reference object with path or registry lookup metadata",
                    },
                    "identifier": {
                        "type": "string",
                        "description": "Component UUID or name",
                    },
                },
                "required": ["identifier"],
                "anyOf": [{"required": ["system_path"]}, {"required": ["model_ref"]}],
            },
        ),
        Tool(
            name="find_orphaned_components",
            description="Find components without substation or feeder assignments.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_path": {
                        "type": "string",
                        "description": "Path to the distribution system JSON file",
                    },
                    "model_ref": {
                        "type": "object",
                        "description": "Model reference object with path or registry lookup metadata",
                    },
                },
                "anyOf": [{"required": ["system_path"]}, {"required": ["model_ref"]}],
            },
        ),
        Tool(
            name="get_component_relationships",
            description="Get parent and child relationships for a component.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_path": {
                        "type": "string",
                        "description": "Path to the distribution system JSON file",
                    },
                    "model_ref": {
                        "type": "object",
                        "description": "Model reference object with path or registry lookup metadata",
                    },
                    "component_id": {
                        "type": "string",
                        "description": "Component UUID or name",
                    },
                },
                "required": ["component_id"],
                "anyOf": [{"required": ["system_path"]}, {"required": ["model_ref"]}],
            },
        ),
        # Utility tools
        Tool(
            name="export_subsystem_by_buses",
            description="Extract a subsystem containing specified buses and their connected components.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_path": {
                        "type": "string",
                        "description": "Path to the distribution system JSON file",
                    },
                    "model_ref": {
                        "type": "object",
                        "description": "Model reference object with path or registry lookup metadata",
                    },
                    "bus_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of bus names to include",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path to save the subsystem",
                    },
                    "name": {
                        "type": "string",
                        "description": "Name for the subsystem",
                    },
                    "keep_timeseries": {
                        "type": "boolean",
                        "description": "Preserve time series (default: true)",
                        "default": True,
                    },
                },
                "required": ["bus_names", "output_path", "name"],
                "anyOf": [{"required": ["system_path"]}, {"required": ["model_ref"]}],
            },
        ),
        Tool(
            name="get_time_series_summary",
            description="Get summary of all time series data in the system.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_path": {
                        "type": "string",
                        "description": "Path to the distribution system JSON file",
                    },
                    "model_ref": {
                        "type": "object",
                        "description": "Model reference object with path or registry lookup metadata",
                    },
                },
                "anyOf": [{"required": ["system_path"]}, {"required": ["model_ref"]}],
            },
        ),
        Tool(
            name="save_system",
            description="Save a distribution system JSON to a target path using DistributionSystem.to_json.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_path": {
                        "type": "string",
                        "description": "Path to source distribution system JSON file",
                    },
                    "model_ref": {
                        "type": "object",
                        "description": "Model reference object with path or registry lookup metadata",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path to write output distribution system JSON file",
                    },
                    "name": {
                        "type": "string",
                        "description": "Optional system name override before saving",
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": "Overwrite output file if it exists (default: false)",
                        "default": False,
                    },
                },
                "required": ["output_path"],
                "anyOf": [{"required": ["system_path"]}, {"required": ["model_ref"]}],
            },
        ),
        # Data / export tools
        Tool(
            name="get_time_series_values",
            description="Get combined time series data for load, solar, or battery components as rows of timestamp/value pairs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_path": {
                        "type": "string",
                        "description": "Path to the distribution system JSON file",
                    },
                    "component_type": {
                        "type": "string",
                        "enum": ["load", "solar", "battery", "all"],
                        "description": "Component type to aggregate (default: all)",
                        "default": "all",
                    },
                    "var_of_interest": {
                        "type": "string",
                        "description": (
                            "Time series variable to return (e.g., 'active_power'). "
                            "Solar time series are stored as 'irradiance' and mapped to 'active_power' "
                            "in the returned rows (default: active_power)"
                        ),
                        "default": "active_power",
                    },
                },
                "required": ["system_path"],
            },
        ),
        Tool(
            name="apply_tracked_changes",
            description="Apply tracked changes (additions, edits, deletions) to a distribution system and save the updated system.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_path": {
                        "type": "string",
                        "description": "Path to the distribution system JSON file",
                    },
                    "tracked_changes_path": {
                        "type": "string",
                        "description": "Path to a JSON file containing a list of TrackedChange objects",
                    },
                    "scenario_name": {
                        "type": "string",
                        "description": "Only apply changes belonging to this scenario (optional)",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path to save the updated system (default: temporary file)",
                    },
                },
                "required": ["system_path", "tracked_changes_path"],
            },
        ),
        Tool(
            name="plot_system",
            description="Generate an interactive HTML plot of the distribution system and optionally export it to a directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_path": {
                        "type": "string",
                        "description": "Path to the distribution system JSON file",
                    },
                    "export_path": {
                        "type": "string",
                        "description": "Directory to save the plot HTML file (created if missing)",
                    },
                    "show": {
                        "type": "boolean",
                        "description": "Open the plot in a browser (default: false)",
                        "default": False,
                    },
                    "color_node_by": {
                        "type": "string",
                        "enum": ["phase", "voltage", "equipment_type"],
                        "description": "Attribute used to color nodes (default: phase)",
                        "default": "phase",
                    },
                    "color_line_by": {
                        "type": "string",
                        "enum": ["phase", "equipment_type"],
                        "description": "Attribute used to color lines (default: equipment_type)",
                        "default": "equipment_type",
                    },
                    "map_type": {
                        "type": "string",
                        "enum": ["scatter_geo", "scatter_mapbox"],
                        "description": "Map type for the plot (default: scatter_geo)",
                        "default": "scatter_geo",
                    },
                },
                "required": ["system_path"],
            },
        ),
        Tool(
            name="to_geojson",
            description="Export the distribution system to a GeoJSON file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_path": {
                        "type": "string",
                        "description": "Path to the distribution system JSON file",
                    },
                    "export_file": {
                        "type": "string",
                        "description": "Path to the output GeoJSON file",
                    },
                },
                "required": ["system_path", "export_file"],
            },
        ),
        # Documentation/Knowledge tools
        Tool(
            name="search_gdm_documentation",
            description="Search grid-data-models documentation for relevant content. Returns snippets from docs, API references, and notebooks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'how to create a bus', 'time series', 'phase')",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_api_reference",
            description="Get detailed API reference for a specific component class (e.g., DistributionBus, DistributionLoad). Returns fields, methods, and usage examples.",
            inputSchema={
                "type": "object",
                "properties": {
                    "component_name": {
                        "type": "string",
                        "description": "Name of the component class (e.g., 'DistributionBus')",
                    }
                },
                "required": ["component_name"],
            },
        ),
        Tool(
            name="get_code_examples",
            description="Get code examples for a specific topic from documentation notebooks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic to search for (e.g., 'creating a bus', 'time series', 'plotting')",
                    }
                },
                "required": ["topic"],
            },
        ),
        Tool(
            name="list_available_components",
            description="List all available distribution component types with descriptions.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_component_fields",
            description="Get detailed field information for a specific component type, including types, requirements, and defaults.",
            inputSchema={
                "type": "object",
                "properties": {
                    "component_name": {
                        "type": "string",
                        "description": "Name of the component class (e.g., 'DistributionBus')",
                    }
                },
                "required": ["component_name"],
            },
        ),
        Tool(
            name="set_tool_calls_enabled",
            description="Enable or disable non-control MCP tool calls at runtime.",
            inputSchema={
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                        "description": "Whether normal tool calls should be enabled",
                    }
                },
                "required": ["enabled"],
            },
        ),
        Tool(
            name="get_tool_calls_enabled",
            description="Get current runtime state for MCP tool-call enablement.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]
    return ListToolsResult(tools=tools)


# Resource definitions
_RESOURCES = [
    Resource(
        uri="gdm://components",
        name="Available Components",
        description="All registered distribution component types",
        mimeType="application/json",
    ),
    Resource(
        uri="gdm://tools",
        name="Available Tools",
        description="All registered MCP tools with descriptions",
        mimeType="application/json",
    ),
    Resource(
        uri="gdm://workflows",
        name="Canonical Workflows",
        description="Pre-defined workflow prompts for common tasks",
        mimeType="application/json",
    ),
]


async def list_resources(ctx: ServerRequestContext, params=None) -> ListResourcesResult:
    """List all available MCP resources."""
    return ListResourcesResult(resources=_RESOURCES)


async def read_resource(ctx: ServerRequestContext, params) -> ReadResourceResult:
    """Read the content of an MCP resource by URI."""
    if params.uri == "gdm://components":
        components = list_components_doc()
        data = [component.model_dump() for component in components]
    elif params.uri == "gdm://tools":
        tools_result = await list_tools(ctx, None)
        data = [{"name": tool.name, "description": tool.description} for tool in tools_result.tools]
    elif params.uri == "gdm://workflows":
        data = [{"name": prompt.name, "description": prompt.description} for prompt in _PROMPTS]
    else:
        raise ValueError(f"Unknown resource: {params.uri}")

    return ReadResourceResult(
        contents=[
            TextResourceContents(
                uri=params.uri,
                text=json.dumps(data, indent=2),
                mimeType="application/json",
            )
        ]
    )


# Prompt definitions
_PROMPTS = [
    Prompt(
        name="validate_and_fix",
        description="Load a system, diagnose issues, suggest fixes, and apply them",
        arguments=[PromptArgument(name="system_path", required=True)],
    ),
    Prompt(
        name="reduce_and_export",
        description="Reduce a distribution system and export to GeoJSON",
        arguments=[
            PromptArgument(name="system_path", required=True),
            PromptArgument(name="export_path", required=True),
        ],
    ),
    Prompt(
        name="analyze_system",
        description="Load a system, get summary, analyze topology, and check time series",
        arguments=[PromptArgument(name="system_path", required=True)],
    ),
]


async def list_prompts(ctx: ServerRequestContext, params=None) -> ListPromptsResult:
    """List all available MCP prompts."""
    return ListPromptsResult(prompts=_PROMPTS)


async def get_prompt(ctx: ServerRequestContext, params) -> GetPromptResult:
    """Get a specific prompt by name."""
    messages = {
        "validate_and_fix": (
            "I'll help you validate and fix a distribution system.\n\n"
            "1. First, call `diagnose_system` with the system path to identify issues.\n"
            "2. Review the diagnostics results.\n"
            "3. Call `suggest_fixes` to get recommended fixes.\n"
            "4. Call `apply_fixes` to apply the fixes.\n"
            "5. Call `get_system_summary` to verify the results."
        ),
        "reduce_and_export": (
            "I'll help you reduce a system and export it.\n\n"
            "1. Call `get_system_summary` to inspect the system.\n"
            "2. Call `reduce_system` to reduce it.\n"
            "3. Call `to_geojson` to export the reduced system.\n"
            "4. Call `save_system` to save the result."
        ),
        "analyze_system": (
            "I'll help you analyze a distribution system.\n\n"
            "1. Call `get_system_summary` for an overview.\n"
            "2. Call `analyze_topology` to check the network structure.\n"
            "3. Call `get_time_series_summary` to check time series data.\n"
            "4. Call `get_component_relationships` to understand component connections."
        ),
    }

    message = messages.get(params.name)
    if message is None:
        raise ValueError(f"Unknown prompt: {params.name}")

    return GetPromptResult(
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=message),
            )
        ]
    )


# Tool dispatch map
_TOOL_HANDLERS: dict[str, Any] = {
    "diagnose_system": lambda args: _diagnose_system(args),
    "suggest_fixes": lambda args: _suggest_fixes(args),
    "apply_fixes": lambda args: _apply_fixes(args),
    "merge_systems": lambda args: _merge_systems(args),
    "split_by_substation": lambda args: _split_by_substation(args),
    "split_by_feeder": lambda args: _split_by_feeder(args),
    "reduce_system": lambda args: _reduce_system(args),
    "get_system_summary": lambda args: _get_system_summary(args),
    "query_components": lambda args: _query_components(args),
    "analyze_topology": lambda args: _analyze_topology(args),
    "validate_connectivity": lambda args: _validate_connectivity(args),
    "get_component_details": lambda args: _get_component_details(args),
    "find_orphaned_components": lambda args: _find_orphaned_components(args),
    "get_component_relationships": lambda args: _get_component_relationships(args),
    "export_subsystem_by_buses": lambda args: _export_subsystem_by_buses(args),
    "get_time_series_summary": lambda args: _get_time_series_summary(args),
    "save_system": lambda args: _save_system(args),
    "get_time_series_values": lambda args: _handle_get_time_series_values(args),
    "apply_tracked_changes": lambda args: _handle_apply_tracked_changes(args),
    "plot_system": lambda args: _handle_plot_system(args),
    "to_geojson": lambda args: _handle_to_geojson(args),
    "search_gdm_documentation": lambda args: _search_gdm_documentation(args),
    "get_api_reference": lambda args: _get_api_reference(args),
    "get_code_examples": lambda args: _get_code_examples(args),
    "list_available_components": lambda args: _list_available_components(args),
    "get_component_fields": lambda args: _get_component_fields(args),
    "set_tool_calls_enabled": lambda args: _set_tool_calls_enabled(args),
    "get_tool_calls_enabled": lambda args: _get_tool_calls_enabled(args),
}


async def call_tool(ctx: ServerRequestContext, params: Any) -> CallToolResult:
    """Handle tool calls from MCP clients."""
    name = params.name
    arguments = params.arguments or {}
    try:
        logger.info(f"Tool called: {name} with arguments: {arguments}")

        if not _TOOL_CALLS_ENABLED and name not in _CONTROL_TOOLS:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "error": (
                                    "Tool calls are currently disabled. "
                                    "Use set_tool_calls_enabled to re-enable."
                                )
                            },
                            indent=2,
                        ),
                    )
                ]
            )

        handler = _TOOL_HANDLERS.get(name)
        if handler is not None:
            result = await handler(arguments)
        else:
            result = {"error": f"Unknown tool: {name}"}

        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        )

    except GDMMCPException as e:
        logger.error(f"GDM MCP error in {name}: {str(e)}")
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))],
            is_error=True,
        )
    except Exception as e:
        logger.error(f"Unexpected error in {name}: {str(e)}", exc_info=True)
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps({"error": f"Unexpected error: {str(e)}"}, indent=2),
                )
            ],
            is_error=True,
        )


# Tool implementations
async def _diagnose_system(args: dict) -> dict:
    """Diagnose system validation errors."""
    system_path = _get_system_path_arg(args)
    system = _load_system_with_fallback_name(system_path)
    report = diagnose_system(system)
    return report.model_dump()


async def _suggest_fixes(args: dict) -> dict:
    """Suggest fixes for validation errors."""
    system_path = _get_system_path_arg(args)
    system = _load_system_with_fallback_name(system_path)
    report = diagnose_system(system)
    suggestions = suggest_fixes(report)
    return {
        "validation_report": report.model_dump(),
        "suggestions": [s.model_dump() for s in suggestions],
    }


async def _apply_fixes(args: dict) -> dict:
    """Apply fixes to a system."""
    system_path = _get_system_path_arg(args)
    output_path = args["output_path"]
    auto_approve = args.get("auto_approve", False)

    system = _load_system_with_fallback_name(system_path)
    report = diagnose_system(system)
    suggestions = suggest_fixes(report)

    fixed_system, fix_result = apply_fixes(system, suggestions, auto_approve)

    # Save fixed system
    fixed_system.to_json(output_path, overwrite=True)

    return {
        "fix_result": fix_result.model_dump(),
        "output_path": output_path,
    }


async def _merge_systems(args: dict) -> dict:
    """Merge multiple systems."""
    system_paths = _get_system_paths_arg(args)
    output_path = args["output_path"]
    name = args["name"]
    strict = args.get("strict", True)

    systems = [_load_system_with_fallback_name(path) for path in system_paths]
    merged_system, report = merge_systems(systems, name, strict)

    # Save merged system
    merged_system.to_json(output_path, overwrite=True)

    return {
        "merge_report": report.model_dump(),
        "output_path": output_path,
    }


async def _split_by_substation(args: dict) -> dict:
    """Split system by substation."""
    system_path = _get_system_path_arg(args)
    output_dir = args["output_dir"]
    keep_timeseries = args.get("keep_timeseries", True)
    include_unassigned = args.get("include_unassigned", True)

    system = _load_system_with_fallback_name(system_path)
    subsystems, report = split_by_substation(system, keep_timeseries, include_unassigned)

    # Save subsystems
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    output_files = {}
    for name, subsystem in subsystems.items():
        output_file = output_dir_path / f"{name}.json"
        subsystem.to_json(str(output_file), overwrite=True)
        output_files[name] = str(output_file)

    return {
        "split_report": report.model_dump(),
        "output_files": output_files,
    }


async def _split_by_feeder(args: dict) -> dict:
    """Split system by feeder."""
    system_path = _get_system_path_arg(args)
    output_dir = args["output_dir"]
    keep_timeseries = args.get("keep_timeseries", True)
    include_unassigned = args.get("include_unassigned", True)

    system = _load_system_with_fallback_name(system_path)
    subsystems, report = split_by_feeder(system, keep_timeseries, include_unassigned)

    # Save subsystems
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    output_files = {}
    for name, subsystem in subsystems.items():
        output_file = output_dir_path / f"{name}.json"
        subsystem.to_json(str(output_file), overwrite=True)
        output_files[name] = str(output_file)

    return {
        "split_report": report.model_dump(),
        "output_files": output_files,
    }


async def _get_system_summary(args: dict) -> dict:
    """Get system summary."""
    system_path = _get_system_path_arg(args)
    system = _load_system_with_fallback_name(system_path)
    summary = get_system_summary(system)
    return summary.model_dump()


async def _query_components(args: dict) -> dict:
    """Query components with filters."""
    system_path = _get_system_path_arg(args)
    system = _load_system_with_fallback_name(system_path)

    filters = ComponentFilter(
        component_types=args.get("component_types"),
        substation=args.get("substation"),
        feeder=args.get("feeder"),
        phases=args.get("phases"),
        in_service=args.get("in_service"),
        has_timeseries=args.get("has_timeseries"),
    )

    components = query_components(system, filters)
    return {"components": [c.model_dump() for c in components], "count": len(components)}


async def _analyze_topology(args: dict) -> dict:
    """Analyze topology."""
    system_path = _get_system_path_arg(args)
    system = _load_system_with_fallback_name(system_path)
    metrics = analyze_topology(system)
    return metrics.model_dump()


async def _validate_connectivity(args: dict) -> dict:
    """Validate connectivity."""
    system_path = _get_system_path_arg(args)
    system = _load_system_with_fallback_name(system_path)
    return validate_connectivity(system)


async def _get_component_details(args: dict) -> dict:
    """Get component details."""
    system_path = _get_system_path_arg(args)
    identifier = args["identifier"]
    system = _load_system_with_fallback_name(system_path)
    return get_component_details(system, identifier)


async def _find_orphaned_components(args: dict) -> dict:
    """Find orphaned components."""
    system_path = _get_system_path_arg(args)
    system = _load_system_with_fallback_name(system_path)
    orphaned = find_orphaned_components(system)
    return {"orphaned_components": [c.model_dump() for c in orphaned], "count": len(orphaned)}


async def _get_component_relationships(args: dict) -> dict:
    """Get component relationships."""
    system_path = _get_system_path_arg(args)
    component_id = args["component_id"]
    system = _load_system_with_fallback_name(system_path)
    relationships = get_component_relationships(system, component_id)
    return {
        "parents": [p.model_dump() for p in relationships.get("parents", [])],
        "children": [c.model_dump() for c in relationships.get("children", [])],
    }


async def _export_subsystem_by_buses(args: dict) -> dict:
    """Export subsystem by buses."""
    system_path = _get_system_path_arg(args)
    bus_names = args["bus_names"]
    output_path = args["output_path"]
    name = args["name"]
    keep_timeseries = args.get("keep_timeseries", True)

    system = _load_system_with_fallback_name(system_path)
    subsystem = export_subsystem_by_buses(system, bus_names, name, keep_timeseries)

    # Save subsystem
    subsystem.to_json(output_path, overwrite=True)

    summary = get_system_summary(subsystem)
    return {
        "output_path": output_path,
        "subsystem_summary": summary.model_dump(),
    }


async def _get_time_series_summary(args: dict) -> dict:
    """Get time series summary."""
    system_path = _get_system_path_arg(args)
    system = _load_system_with_fallback_name(system_path)
    return get_time_series_summary(system)


# Documentation/Knowledge handlers
async def _search_gdm_documentation(args: dict) -> dict:
    """Search GDM documentation."""
    query = args["query"]
    max_results = args.get("max_results", 5)

    results = search_documentation(query, max_results)
    return {"query": query, "results": [r.model_dump() for r in results]}


async def _get_api_reference(args: dict) -> dict:
    """Get API reference for a component."""
    component_name = args["component_name"]
    result = get_api_ref(component_name)
    return result.model_dump()


async def _get_code_examples(args: dict) -> dict:
    """Get code examples for a topic."""
    topic = args["topic"]
    examples = get_code_ex(topic)
    return {"topic": topic, "examples": [e.model_dump() for e in examples]}


async def _list_available_components(args: dict) -> dict:
    """List available components."""
    components = list_components_doc()
    return {"components": [c.model_dump() for c in components]}


async def _get_component_fields(args: dict) -> dict:
    """Get component field information."""
    component_name = args["component_name"]
    fields = get_fields_doc(component_name)
    return {"component_name": component_name, "fields": fields}


async def _save_system(args: dict) -> dict:
    """Save a distribution system JSON to a target path."""
    system_path = _get_system_path_arg(args)
    output_path = args["output_path"]
    overwrite = args.get("overwrite", False)

    output_file = Path(output_path)
    if output_file.exists() and not overwrite:
        raise ValueError(
            f"Output file already exists: {output_path}. Set overwrite=true to replace."
        )

    system = _load_system_with_fallback_name(system_path)
    if args.get("name") is not None:
        system.name = args["name"]

    system.to_json(output_path, overwrite=overwrite)
    result = {
        "output_path": output_path,
        "name": system.name,
    }
    record = None
    if os.getenv("DIST_STACK_MODEL_REGISTRY_DB"):
        record = register(
            model_id=args.get("model_id") or make_model_id(output_path),
            version=args.get("version"),
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


# Data / export handlers
def _json_safe(value: Any) -> Any:
    """Coerce pandas/numpy/UUID/quantity values into JSON-serializable primitives."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Quantity):
        magnitude = value.magnitude
        return magnitude.tolist() if isinstance(magnitude, np.ndarray) else float(magnitude)
    if isinstance(value, (pd.Timestamp, pd.Timedelta)):
        return value.isoformat()
    if isinstance(value, timedelta):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    return value


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


async def _handle_get_time_series_values(args: dict) -> dict:
    """Get combined time series values for load, solar, battery, or all components."""
    system_path = _get_system_path_arg(args)
    component_type = args.get("component_type", "all")
    var_of_interest = args.get("var_of_interest", "active_power")

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


async def _handle_apply_tracked_changes(args: dict) -> dict:
    """Apply tracked changes to a distribution system and save the updated system."""
    system_path = _get_system_path_arg(args)
    tracked_changes_path = args["tracked_changes_path"]
    scenario_name = args.get("scenario_name")
    output_path = args.get("output_path")

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


async def _handle_plot_system(args: dict) -> dict:
    """Generate an interactive HTML plot of the distribution system."""
    system_path = _get_system_path_arg(args)
    export_path = args.get("export_path")
    show = bool(args.get("show", False))
    color_node_by = args.get("color_node_by", "phase")
    color_line_by = args.get("color_line_by", "equipment_type")
    map_type = args.get("map_type", "scatter_geo")

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


async def _handle_to_geojson(args: dict) -> dict:
    """Export the distribution system to a GeoJSON file."""
    system_path = _get_system_path_arg(args)
    export_file = args["export_file"]

    system = _load_system_with_fallback_name(system_path)
    system.to_geojson(export_file)

    return {"output_path": str(export_file), "message": f"GeoJSON exported to {export_file}"}


async def _set_tool_calls_enabled(args: dict) -> dict:
    """Set runtime MCP tool-call enablement state."""
    global _TOOL_CALLS_ENABLED

    _TOOL_CALLS_ENABLED = bool(args["enabled"])
    return {
        "tool_calls_enabled": _TOOL_CALLS_ENABLED,
        "message": (
            "Non-control tool calls are enabled"
            if _TOOL_CALLS_ENABLED
            else "Non-control tool calls are disabled"
        ),
    }


async def _get_tool_calls_enabled(args: dict) -> dict:
    """Get runtime MCP tool-call enablement state."""
    return {"tool_calls_enabled": _TOOL_CALLS_ENABLED}


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

    global _TOOL_CALLS_ENABLED
    _TOOL_CALLS_ENABLED = tool_calls_enabled

    # Run the server
    import asyncio

    app = Server(
        "grid-data-models-mcp",
        version=__version__,
        on_list_tools=list_tools,
        on_call_tool=call_tool,
        on_list_resources=list_resources,
        on_read_resource=read_resource,
        on_list_prompts=list_prompts,
        on_get_prompt=get_prompt,
    )

    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(run())


async def _reduce_system(args: dict) -> dict:
    """Reduce a distribution system model."""
    system_path = _get_system_path_arg(args)
    output_path = args["output_path"]
    reducer = args.get("reducer", "three_phase")
    keep_timeseries = args.get("keep_timeseries", False)
    overwrite = args.get("overwrite", False)

    output_file = Path(output_path)
    if output_file.exists() and not overwrite:
        raise ValueError(
            f"Output file already exists: {output_path}. Set overwrite=true to replace."
        )

    system = _load_system_with_fallback_name(system_path)
    reduced_name = args.get("name") or f"{system.name}_reduced"

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


def main():
    typer.run(_run_server)


if __name__ == "__main__":
    main()
