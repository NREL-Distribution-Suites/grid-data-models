

[![Upload to PyPi](https://github.com/NLR-Distribution-Suite/grid-data-models/actions/workflows/publish_to_pypi.yml/badge.svg)](https://github.com/NLR-Distribution-Suite/grid-data-models/actions/workflows/publish_to_pypi.yml) •  [![Pytest](https://github.com/NLR-Distribution-Suite/grid-data-models/actions/workflows/pull_request_tests.yml/badge.svg)](https://github.com/NLR-Distribution-Suite/grid-data-models/actions/workflows/pull_request_tests.yml) •  [![deploy-book](https://github.com/NLR-Distribution-Suite/grid-data-models/actions/workflows/deploy.yml/badge.svg)](https://github.com/NLR-Distribution-Suite/grid-data-models/actions/workflows/deploy.yml) • ![PyPI - Downloads](https://img.shields.io/pypi/dm/grid-data-models) •  [![codecov](https://codecov.io/github/NLR-Distribution-Suite/grid-data-models/branch/main/graph/badge.svg?token=K0X11EXOX8)](https://codecov.io/github/NLR-Distribution-Suite/grid-data-models) •  [![CodeFactor](https://www.codefactor.io/repository/github/nlr-distribution-suite/grid-data-models/badge)](https://www.codefactor.io/repository/github/nlr-distribution-suite/grid-data-models) • ![MCP Server](https://img.shields.io/badge/MCP_Server-enabled-brightgreen) • ![MCP Tools](https://img.shields.io/badge/MCP_Tools-24-blue) • [![GitHub issues](https://img.shields.io/github/issues/NLR-Distribution-Suite/grid-data-models)](https://github.com/NLR-Distribution-Suite/grid-data-models/issues) • [![License](https://img.shields.io/github/license/NLR-Distribution-Suite/grid-data-models)](https://github.com/NLR-Distribution-Suite/grid-data-models/blob/main/LICENSE.txt) •  [![PyPI Downloads](https://static.pepy.tech/personalized-badge/grid-data-models?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/grid-data-models) • [![Generate LinkedIn Post Draft](https://github.com/NLR-Distribution-Suite/grid-data-models/actions/workflows/linkedin_draft.yml/badge.svg)](https://github.com/NLR-Distribution-Suite/grid-data-models/actions/workflows/linkedin_draft.yml)

# Grid Data Models (GDM)

GDM is a python package containing data models for power system assets and datasets. This package is actively being developed at [National Renewable Energy Laboratory (NREL)](https://www.nrel.gov/).

## Installation

You can install the latest version of `grid-data-models` from PyPi.

```bash
pip install grid-data-models
```

## Why Grid Data Models?

In an effort to reduce code duplication and provide client packages a standard interface to interact with power system data, a group of research engineers at NREL is working on developing standard data models. Features:

- **Built-in validation layer:** Use of [pydantic](https://docs.pydantic.dev/latest/) allows us to validate model fields.
- **Time series data management:** GDM uses [infrasys](https://github.nrel.gov/CADET/infrastructure_systems) package which enables [efficient time series data management](https://nrel.github.io/infrasys/explanation/time_series.html) by sharing arrays across components and offloading system memory. For example, we can attach time series power consumption data to a load profile.
- **Built-in unit conversion:** GDM leverages [pint](https://pint.readthedocs.io/en/stable/) for unit conversion for power system quantities. For example, power, voltage, time, etc.
- **JSON serialization/deserialization:** GDM uses [infrasys](https://github.com/NatLabRockies/infrasys) to serialize and deserialize distribution system components to/from JSON.
- **Track System Changes:** Supports tracking changes within a distribution model (both temporal and scenario-based static updates), enabling powerful scenario management capabilities.
- **Graph-Based Analysis:** Exposes a connectivity graph using NetworkX, allowing advanced graph-based algorithms and visualizations.
- **Interoperability:** Easily integrates with existing tools.
- **Model reduction:** Built-in support for multiple model reduction algorithms.

## How to get started?

To get started, you can clone and pip install this library from [here](https://nrel-distribution-suites.github.io/grid-data-models/).

## Model Context Protocol (MCP) Integration

GDM includes an MCP server that enables AI assistants to interact with power system models through natural language. The MCP integration provides:

- **System inspection and analysis** - Query components, analyze topology, validate connectivity
- **Validation and diagnostics** - Diagnose errors, suggest fixes, and automatically apply corrections
- **System operations** - Merge, split, and extract subsystems
- **Documentation and API access** - Search documentation and get component API references

To install with MCP support:

```bash
pip install -e ".[mcp]"
```

To run the MCP server:

```bash
gdm-mcp-server
```

For more details, see the [MCP documentation](docs/mcp/).

<!-- MCP-TOOLS:START -->

### MCP Tools (24)

| Tool | Description |
| --- | --- |
| `analyze_topology` | Analyze network topology: node/edge counts, cycles, islands, radial check, source bus. |
| `apply_fixes` | Automatically apply fixes to a distribution system. Creates a fixed copy and returns change log. |
| `diagnose_system` | Diagnose validation errors in a distribution system. Returns detailed error report with component UUIDs, error types, and affected fields. |
| `export_subsystem_by_buses` | Extract a subsystem containing specified buses and their connected components. |
| `find_orphaned_components` | Find components without substation or feeder assignments. |
| `get_api_reference` | Get detailed API reference for a specific component class (e.g., DistributionBus, DistributionLoad). Returns fields, methods, and usage examples. |
| `get_code_examples` | Get code examples for a specific topic from documentation notebooks. |
| `get_component_details` | Get detailed information about a specific component by UUID or name. |
| `get_component_fields` | Get detailed field information for a specific component type, including types, requirements, and defaults. |
| `get_component_relationships` | Get parent and child relationships for a component. |
| `get_system_summary` | Get comprehensive summary of a distribution system including component counts, substations, feeders, and time series. |
| `get_time_series_summary` | Get summary of all time series data in the system. |
| `get_tool_calls_enabled` | Get current runtime state for MCP tool-call enablement. |
| `list_available_components` | List all available distribution component types with descriptions. |
| `merge_systems` | Merge multiple distribution systems into one. Preserves time series and detects conflicts. |
| `query_components` | Query and filter components in a distribution system by type, substation, feeder, phases, etc. |
| `reduce_system` | Reduce a distribution system model (supports three-phase and primary reduction). |
| `save_system` | Save a distribution system JSON to a target path using DistributionSystem.to_json. |
| `search_gdm_documentation` | Search grid-data-models documentation for relevant content. Returns snippets from docs, API references, and notebooks. |
| `set_tool_calls_enabled` | Enable or disable non-control MCP tool calls at runtime. |
| `split_by_feeder` | Split a distribution system into separate systems for each feeder. |
| `split_by_substation` | Split a distribution system into separate systems for each substation. |
| `suggest_fixes` | Generate fix suggestions for validation errors. Analyzes error report and proposes strategies with confidence levels. |
| `validate_connectivity` | Validate that all buses are reachable from the source bus. Identifies islands and unreachable components. |

<!-- MCP-TOOLS:END -->


## Contributors

- **Aadil Latif**
- **Daniel Thom**
- **Jeremy Keen**
- **Kapil Duwadi**
- **Tarek Elgindy**
- **Pedro Andres Sanchez Perez**
