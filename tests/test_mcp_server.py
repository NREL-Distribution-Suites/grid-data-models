"""Tests for MCP server helpers."""

import asyncio
import json
import os
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

import gdm.mcp.server as mcp_server
import pytest
from dist_stack.registry import register
from gdm.mcp.server import _load_system_with_fallback_name
from gdm.distribution import DistributionSystem
from gdm.distribution.components import DistributionBus, DistributionVoltageSource
from gdm.distribution.equipment import PhaseCapacitorEquipment
from gdm.quantities import ReactivePower
from gdm.tracked_changes import TrackedChange, PropertyEdit


def _make_call_tool_params(name: str, arguments: dict | None = None):
    """Create a mock CallToolRequestParams for testing."""
    params = MagicMock()
    params.name = name
    params.arguments = arguments or {}
    return params


def _call_tool(name: str, arguments: dict | None = None):
    """Helper to call tool_handler with mock context."""
    ctx = MagicMock()
    params = _make_call_tool_params(name, arguments)
    result = asyncio.run(mcp_server.call_tool(ctx, params))
    return result


def test_load_system_with_fallback_name_for_null_name(simple_system, tmp_path):
    """Falls back to file stem when serialized system name is null."""
    system_path = tmp_path / "null_name_system.json"
    simple_system.to_json(str(system_path), overwrite=True)

    data = json.loads(system_path.read_text())
    data["name"] = None
    system_path.write_text(json.dumps(data))

    loaded_system = _load_system_with_fallback_name(str(system_path))

    assert loaded_system.name == "null_name_system"


def test_load_system_with_fallback_name_for_blank_name(simple_system, tmp_path):
    """Falls back to file stem when serialized system name is blank."""
    system_path = tmp_path / "blank_name_system.json"
    simple_system.to_json(str(system_path), overwrite=True)

    data = json.loads(system_path.read_text())
    data["name"] = "   "
    system_path.write_text(json.dumps(data))

    loaded_system = _load_system_with_fallback_name(str(system_path))

    assert loaded_system.name == "blank_name_system"


def test_load_system_with_fallback_name_preserves_valid_name(simple_system, tmp_path):
    """Keeps an existing valid system name unchanged."""
    system_path = tmp_path / "valid_name_system.json"
    simple_system.to_json(str(system_path), overwrite=True)

    loaded_system = _load_system_with_fallback_name(str(system_path))

    assert loaded_system.name == "test_system"


def test_get_system_summary_accepts_model_ref_with_direct_path(simple_system, tmp_path):
    """Path-carrying model_ref should work for path-based handlers."""
    system_path = tmp_path / "direct_ref_system.json"
    simple_system.to_json(str(system_path), overwrite=True)

    result = asyncio.run(mcp_server._get_system_summary({"model_ref": {"path": str(system_path)}}))

    assert result["name"] == "test_system"


def test_get_system_summary_accepts_model_ref_via_registry_db(simple_system, tmp_path):
    """model_ref with model_id/version should resolve through registry DB."""
    system_path = tmp_path / "registry_ref_system.json"
    simple_system.to_json(str(system_path), overwrite=True)

    db_path = tmp_path / "registry.sqlite"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE models (
                model_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                stored_path TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO models (model_id, version, stored_path) VALUES (?, ?, ?)",
            ("abc123", 1, str(system_path)),
        )

    os.environ["DIST_STACK_MODEL_REGISTRY_DB"] = str(db_path)
    try:
        result = asyncio.run(
            mcp_server._get_system_summary({"model_ref": {"model_id": "abc123", "version": 1}})
        )
    finally:
        os.environ.pop("DIST_STACK_MODEL_REGISTRY_DB", None)

    assert result["name"] == "test_system"


def test_get_system_summary_accepts_model_ref_registered_via_library(simple_system, tmp_path):
    """model_ref registered through the dist_stack library should resolve."""
    system_path = tmp_path / "lib_registry_system.json"
    simple_system.to_json(str(system_path), overwrite=True)

    db_path = tmp_path / "lib_registry.sqlite"
    os.environ["DIST_STACK_MODEL_REGISTRY_DB"] = str(db_path)
    try:
        record = register(
            model_id="lib_model_1",
            version=2,
            stored_path=str(system_path),
            metadata={"tool": "test"},
        )
        result = asyncio.run(
            mcp_server._get_system_summary(
                {"model_ref": {"model_id": "lib_model_1", "version": 2}}
            )
        )
    finally:
        os.environ.pop("DIST_STACK_MODEL_REGISTRY_DB", None)

    assert record.model_id == "lib_model_1"
    assert record.version == 2
    assert result["name"] == "test_system"


def test_get_tool_calls_enabled_reports_current_state():
    """Control status tool should report current runtime toggle state."""
    mcp_server._TOOL_CALLS_ENABLED = True

    response = _call_tool("get_tool_calls_enabled", {})
    payload = json.loads(response.content[0].text)

    assert payload["tool_calls_enabled"] is True


def test_set_tool_calls_enabled_disables_non_control_calls():
    """Disabling should block normal tools while allowing control tools."""
    mcp_server._TOOL_CALLS_ENABLED = True

    disable_response = _call_tool("set_tool_calls_enabled", {"enabled": False})
    disable_payload = json.loads(disable_response.content[0].text)
    assert disable_payload["tool_calls_enabled"] is False

    blocked_response = _call_tool("unknown_normal_tool", {})
    blocked_payload = json.loads(blocked_response.content[0].text)
    assert "disabled" in blocked_payload["error"].lower()

    # Control tools remain callable so clients can re-enable.
    status_response = _call_tool("get_tool_calls_enabled", {})
    status_payload = json.loads(status_response.content[0].text)
    assert status_payload["tool_calls_enabled"] is False


def test_set_tool_calls_enabled_can_reenable():
    """Re-enabling should restore normal call flow."""
    mcp_server._TOOL_CALLS_ENABLED = False

    enable_response = _call_tool("set_tool_calls_enabled", {"enabled": True})
    enable_payload = json.loads(enable_response.content[0].text)

    assert enable_payload["tool_calls_enabled"] is True

    unknown_response = _call_tool("unknown_normal_tool", {})
    unknown_payload = json.loads(unknown_response.content[0].text)
    assert "unknown tool" in unknown_payload["error"].lower()


def test_list_tools_includes_reduce_system():
    """Tool list should expose model-reduction capability."""
    ctx = MagicMock()
    result = asyncio.run(mcp_server.list_tools(ctx, None))
    tool_names = {tool.name for tool in result.tools}

    assert "reduce_system" in tool_names
    assert "save_system" in tool_names


def test_reduce_system_creates_output_and_summary(simple_system, tmp_path):
    """reduce_system should write a reduced model and return summary payload."""
    source_path = tmp_path / "source.json"
    reducible_system = _make_reducible_system(simple_system)
    reducible_system.to_json(str(source_path), overwrite=True)
    output_path = tmp_path / "reduced.json"

    result = asyncio.run(
        mcp_server._reduce_system(
            {
                "system_path": str(source_path),
                "output_path": str(output_path),
                "reducer": "three_phase",
            }
        )
    )

    assert output_path.exists()
    assert result["output_path"] == str(output_path)
    assert result["reducer"] == "three_phase"
    assert result["summary"]["name"].endswith("_reduced")


def test_reduce_system_supports_primary_reducer(simple_system, tmp_path):
    """reduce_system should support primary voltage reduction."""
    source_path = tmp_path / "source.json"
    reducible_system = _make_reducible_system(simple_system)
    reducible_system.to_json(str(source_path), overwrite=True)
    output_path = tmp_path / "reduced_primary.json"

    result = asyncio.run(
        mcp_server._reduce_system(
            {
                "system_path": str(source_path),
                "output_path": str(output_path),
                "reducer": "primary",
            }
        )
    )

    assert output_path.exists()
    assert result["reducer"] == "primary"


def test_reduce_system_requires_overwrite_for_existing_target(simple_system, tmp_path):
    """reduce_system should fail when output exists and overwrite is false."""
    source_path = tmp_path / "source.json"
    reducible_system = _make_reducible_system(simple_system)
    reducible_system.to_json(str(source_path), overwrite=True)
    output_path = tmp_path / "reduced.json"
    output_path.write_text("{}")

    with pytest.raises(ValueError, match="Output file already exists"):
        asyncio.run(
            mcp_server._reduce_system(
                {
                    "system_path": str(source_path),
                    "output_path": str(output_path),
                }
            )
        )


def test_save_system_writes_output_with_name_override(simple_system, tmp_path):
    """save_system should write output JSON and optionally override system name."""
    source_path = tmp_path / "source.json"
    simple_system.to_json(str(source_path), overwrite=True)
    output_path = tmp_path / "saved.json"

    result = asyncio.run(
        mcp_server._save_system(
            {
                "system_path": str(source_path),
                "output_path": str(output_path),
                "name": "saved_system",
            }
        )
    )

    assert output_path.exists()
    assert result["output_path"] == str(output_path)
    assert result["name"] == "saved_system"


def test_save_system_writes_provenance_manifest_sidecar(simple_system, tmp_path):
    """save_system should write a .manifest.json sidecar next to the output."""
    source_path = tmp_path / "source.json"
    simple_system.to_json(str(source_path), overwrite=True)
    output_path = tmp_path / "saved_manifest.json"

    result = asyncio.run(
        mcp_server._save_system(
            {
                "system_path": str(source_path),
                "output_path": str(output_path),
            }
        )
    )

    manifest_path = Path(f"{output_path}.manifest.json")
    assert manifest_path.exists()
    assert result["output_path"] == str(output_path)

    manifest = json.loads(manifest_path.read_text())
    assert manifest["artifact_type"] == "gdm_system"
    assert manifest["tool"] == "save_system"
    assert manifest["artifact_path"] == str(output_path)


def test_save_system_requires_overwrite_for_existing_target(simple_system, tmp_path):
    """save_system should fail when output exists and overwrite is false."""
    source_path = tmp_path / "source.json"
    simple_system.to_json(str(source_path), overwrite=True)
    output_path = tmp_path / "saved.json"
    output_path.write_text("{}")

    with pytest.raises(ValueError, match="Output file already exists"):
        asyncio.run(
            mcp_server._save_system(
                {
                    "system_path": str(source_path),
                    "output_path": str(output_path),
                }
            )
        )


def _make_reducible_system(simple_system):
    """Attach a voltage source so reducer graph traversal can establish source bus."""
    buses = list(simple_system.get_components(DistributionBus))
    source_bus = buses[0]

    vsource = DistributionVoltageSource.example().model_copy(
        update={
            "name": "test_source",
            "bus": source_bus,
            "phases": source_bus.phases,
            "substation": source_bus.substation,
            "feeder": source_bus.feeder,
        }
    )
    simple_system.add_component(vsource)
    return simple_system


def test_get_time_series_values(distribution_system_with_single_time_series, tmp_path):
    """get_time_series_values should return combined time series rows for load components."""
    system_path = tmp_path / "ts_system.json"
    distribution_system_with_single_time_series.to_json(str(system_path), overwrite=True)

    result = asyncio.run(
        mcp_server._handle_get_time_series_values(
            {
                "system_path": str(system_path),
                "component_type": "load",
                "var_of_interest": "active_power",
            }
        )
    )

    assert result["component_type"] == "load"
    assert result["count"] > 0
    assert "timestamp" in result["columns"]
    assert "value" in result["columns"]
    assert all(row["name"] == "active_power" for row in result["rows"])


def test_get_time_series_values_supports_solar(
    distribution_system_with_single_time_series, tmp_path
):
    """get_time_series_values should return combined solar time series rows (irradiance -> active_power)."""
    system_path = tmp_path / "ts_system_solar.json"
    distribution_system_with_single_time_series.to_json(str(system_path), overwrite=True)

    result = asyncio.run(
        mcp_server._handle_get_time_series_values(
            {
                "system_path": str(system_path),
                "component_type": "solar",
                "var_of_interest": "active_power",
            }
        )
    )

    assert result["component_type"] == "solar"
    assert result["count"] > 0
    assert all(row["name"] == "active_power" for row in result["rows"])


def test_apply_tracked_changes(distribution_system_with_single_time_series, tmp_path):
    """apply_tracked_changes should apply tracked edits and save the updated system."""
    system_path = tmp_path / "base_system.json"
    distribution_system_with_single_time_series.to_json(str(system_path), overwrite=True)

    capacitor = next(
        distribution_system_with_single_time_series.get_components(PhaseCapacitorEquipment)
    )
    changes = [
        TrackedChange(
            scenario_name="scenario_1",
            timestamp="2022-01-01 00:00:00",
            edits=[
                PropertyEdit(
                    component_uuid=capacitor.uuid,
                    name="rated_reactive_power",
                    value=ReactivePower(200, "kvar"),
                )
            ],
        ),
        TrackedChange(
            scenario_name="scenario_1",
            timestamp="2023-01-01 00:00:00",
            edits=[
                PropertyEdit(
                    component_uuid=capacitor.uuid,
                    name="rated_reactive_power",
                    value=ReactivePower(300, "kvar"),
                )
            ],
        ),
    ]
    changes_path = tmp_path / "changes.json"
    mcp_server._save_tracked_changes(changes, str(changes_path))

    output_path = tmp_path / "updated_system.json"
    result = asyncio.run(
        mcp_server._handle_apply_tracked_changes(
            {
                "system_path": str(system_path),
                "tracked_changes_path": str(changes_path),
                "scenario_name": "scenario_1",
                "output_path": str(output_path),
            }
        )
    )

    assert output_path.exists()
    assert result["output_path"] == str(output_path)
    assert result["scenario_name"] == "scenario_1"
    assert result["changes_applied"] == 2

    updated_system = DistributionSystem.from_json(str(output_path))
    updated_capacitor = updated_system.get_component_by_uuid(capacitor.uuid)
    assert updated_capacitor.rated_reactive_power.to("kilovar").magnitude == 300.0


def test_plot_system(distribution_system_with_single_time_series, tmp_path):
    """plot_system should generate an interactive HTML plot file."""
    system_path = tmp_path / "plot_system.json"
    distribution_system_with_single_time_series.to_json(str(system_path), overwrite=True)
    export_dir = tmp_path / "plots"

    result = asyncio.run(
        mcp_server._handle_plot_system(
            {"system_path": str(system_path), "export_path": str(export_dir)}
        )
    )

    assert result["output_path"].endswith(".html")
    assert Path(result["output_path"]).exists()


def test_to_geojson(distribution_system_with_single_time_series, tmp_path):
    """to_geojson should export the system to a GeoJSON file."""
    system_path = tmp_path / "geo_system.json"
    distribution_system_with_single_time_series.to_json(str(system_path), overwrite=True)
    export_file = tmp_path / "system.geojson"

    result = asyncio.run(
        mcp_server._handle_to_geojson(
            {"system_path": str(system_path), "export_file": str(export_file)}
        )
    )

    assert export_file.exists()
    assert result["output_path"] == str(export_file)


def test_list_resources():
    """list_resources should return the three canonical resources."""
    ctx = MagicMock()
    result = asyncio.run(mcp_server.list_resources(ctx, None))
    uris = {resource.uri for resource in result.resources}

    assert len(result.resources) == 3
    assert uris == {"gdm://components", "gdm://tools", "gdm://workflows"}


def test_read_resources():
    """read_resource should return valid JSON for each resource URI."""
    ctx = MagicMock()
    for uri in ("gdm://components", "gdm://tools", "gdm://workflows"):
        params = MagicMock()
        params.uri = uri
        result = asyncio.run(mcp_server.read_resource(ctx, params))

        assert result.contents[0].uri == uri
        assert result.contents[0].mime_type == "application/json"
        payload = json.loads(result.contents[0].text)
        assert isinstance(payload, list)
        assert len(payload) > 0


def test_list_prompts():
    """list_prompts should return the three canonical prompts."""
    ctx = MagicMock()
    result = asyncio.run(mcp_server.list_prompts(ctx, None))
    names = {prompt.name for prompt in result.prompts}

    assert len(result.prompts) == 3
    assert names == {"validate_and_fix", "reduce_and_export", "analyze_system"}


def test_get_prompts():
    """get_prompt should return the step-by-step instruction message for each prompt."""
    ctx = MagicMock()
    for name in ("validate_and_fix", "reduce_and_export", "analyze_system"):
        params = MagicMock()
        params.name = name
        result = asyncio.run(mcp_server.get_prompt(ctx, params))

        assert len(result.messages) == 1
        message = result.messages[0]
        assert message.role == "user"
        assert message.content.type == "text"
        assert "1." in message.content.text
