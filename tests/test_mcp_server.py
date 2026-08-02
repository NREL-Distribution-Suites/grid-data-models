"""Tests for MCP server helpers."""

import asyncio
import json
import os
import sqlite3
from pathlib import Path

import gdm.mcp.tools.control as control
import pytest
from dist_stack.registry import register
from gdm.distribution import DistributionSystem
from gdm.distribution.components import DistributionBus, DistributionVoltageSource
from gdm.distribution.equipment import PhaseCapacitorEquipment
from gdm.mcp.common import _load_system_with_fallback_name
from gdm.mcp.server import create_server
from gdm.mcp.tools.tracked_changes import _save_tracked_changes
from gdm.quantities import ReactivePower
from gdm.tracked_changes import TrackedChange, PropertyEdit


_server = create_server()


def _tool(tool_name: str):
    """Get the registered (guard-wrapped) tool function by name."""
    return _server._tool_manager._tools[tool_name].fn


def _call_tool(tool_name: str, **kwargs):
    """Call a registered tool function directly with keyword arguments."""
    return asyncio.run(_tool(tool_name)(**kwargs))


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

    result = _call_tool("get_system_summary", model_ref={"path": str(system_path)})

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
        result = _call_tool(
            "get_system_summary", model_ref={"model_id": "abc123", "version": 1}
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
        result = _call_tool(
            "get_system_summary", model_ref={"model_id": "lib_model_1", "version": 2}
        )
    finally:
        os.environ.pop("DIST_STACK_MODEL_REGISTRY_DB", None)

    assert record.model_id == "lib_model_1"
    assert record.version == 2
    assert result["name"] == "test_system"


def test_get_tool_calls_enabled_reports_current_state():
    """Control status tool should report current runtime toggle state."""
    control._TOOL_CALLS_ENABLED = True

    payload = _call_tool("get_tool_calls_enabled")

    assert payload["tool_calls_enabled"] is True


def test_set_tool_calls_enabled_disables_non_control_calls():
    """Disabling should block normal tools while allowing control tools."""
    control._TOOL_CALLS_ENABLED = True

    disable_payload = _call_tool("set_tool_calls_enabled", enabled=False)
    assert disable_payload["tool_calls_enabled"] is False

    blocked_payload = _call_tool("list_available_components")
    assert "disabled" in blocked_payload["error"].lower()

    # Control tools remain callable so clients can re-enable.
    status_payload = _call_tool("get_tool_calls_enabled")
    assert status_payload["tool_calls_enabled"] is False


def test_set_tool_calls_enabled_can_reenable():
    """Re-enabling should restore normal call flow."""
    control._TOOL_CALLS_ENABLED = False

    enable_payload = _call_tool("set_tool_calls_enabled", enabled=True)
    assert enable_payload["tool_calls_enabled"] is True

    # A non-control tool works again after re-enabling.
    payload = _call_tool("list_available_components")
    assert "components" in payload


@pytest.mark.parametrize(
    "tool_name,kwargs",
    [
        ("diagnose_system", {"system_path": "x.json"}),
        ("merge_systems", {"system_paths": ["a.json", "b.json"]}),
        ("get_system_summary", {"system_path": "x.json"}),
        ("to_geojson", {"system_path": "x.json", "export_file": "out.geojson"}),
        ("apply_tracked_changes", {"system_path": "x.json", "tracked_changes_path": "c.json"}),
        ("search_gdm_documentation", {"query": "bus"}),
    ],
)
def test_guard_returns_disabled_payload_for_every_module(tool_name, kwargs):
    """Every non-control module's tools return the disabled payload while toggled off."""
    control._TOOL_CALLS_ENABLED = False
    try:
        payload = _call_tool(tool_name, **kwargs)
        assert "disabled" in payload["error"].lower()
    finally:
        control._TOOL_CALLS_ENABLED = True


def test_list_tools_includes_reduce_system():
    """Tool list should expose model-reduction capability."""
    server = create_server()
    tool_names = {tool.name for tool in asyncio.run(server.list_tools())}

    assert "reduce_system" in tool_names
    assert "save_system" in tool_names


def test_reduce_system_creates_output_and_summary(simple_system, tmp_path):
    """reduce_system should write a reduced model and return summary payload."""
    source_path = tmp_path / "source.json"
    reducible_system = _make_reducible_system(simple_system)
    reducible_system.to_json(str(source_path), overwrite=True)
    output_path = tmp_path / "reduced.json"

    result = _call_tool(
        "reduce_system",
        system_path=str(source_path),
        output_path=str(output_path),
        reducer="three_phase",
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

    result = _call_tool(
        "reduce_system",
        system_path=str(source_path),
        output_path=str(output_path),
        reducer="primary",
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
        _call_tool("reduce_system", system_path=str(source_path), output_path=str(output_path))


def test_save_system_writes_output_with_name_override(simple_system, tmp_path):
    """save_system should write output JSON and optionally override system name."""
    source_path = tmp_path / "source.json"
    simple_system.to_json(str(source_path), overwrite=True)
    output_path = tmp_path / "saved.json"

    result = _call_tool(
        "save_system",
        system_path=str(source_path),
        output_path=str(output_path),
        name="saved_system",
    )

    assert output_path.exists()
    assert result["output_path"] == str(output_path)
    assert result["name"] == "saved_system"


def test_save_system_writes_provenance_manifest_sidecar(simple_system, tmp_path):
    """save_system should write a .manifest.json sidecar next to the output."""
    source_path = tmp_path / "source.json"
    simple_system.to_json(str(source_path), overwrite=True)
    output_path = tmp_path / "saved_manifest.json"

    result = _call_tool("save_system", system_path=str(source_path), output_path=str(output_path))

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
        _call_tool("save_system", system_path=str(source_path), output_path=str(output_path))


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

    result = _call_tool(
        "get_time_series_values",
        system_path=str(system_path),
        component_type="load",
        var_of_interest="active_power",
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

    result = _call_tool(
        "get_time_series_values",
        system_path=str(system_path),
        component_type="solar",
        var_of_interest="active_power",
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
    _save_tracked_changes(changes, str(changes_path))

    output_path = tmp_path / "updated_system.json"
    result = _call_tool(
        "apply_tracked_changes",
        system_path=str(system_path),
        tracked_changes_path=str(changes_path),
        scenario_name="scenario_1",
        output_path=str(output_path),
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

    result = _call_tool(
        "plot_system", system_path=str(system_path), export_path=str(export_dir)
    )

    assert result["output_path"].endswith(".html")
    assert Path(result["output_path"]).exists()


def test_to_geojson(distribution_system_with_single_time_series, tmp_path):
    """to_geojson should export the system to a GeoJSON file."""
    system_path = tmp_path / "geo_system.json"
    distribution_system_with_single_time_series.to_json(str(system_path), overwrite=True)
    export_file = tmp_path / "system.geojson"

    result = _call_tool("to_geojson", system_path=str(system_path), export_file=str(export_file))

    assert export_file.exists()
    assert result["output_path"] == str(export_file)


def test_list_resources():
    """list_resources should return the three canonical resources."""
    server = create_server()
    resources = asyncio.run(server.list_resources())
    uris = {resource.uri for resource in resources}

    assert len(resources) == 3
    assert uris == {"gdm://components", "gdm://tools", "gdm://workflows"}


def test_read_resources():
    """read_resource should return valid JSON for each resource URI."""
    server = create_server()
    for uri in ("gdm://components", "gdm://tools", "gdm://workflows"):
        contents = list(asyncio.run(server.read_resource(uri)))

        assert contents[0].mime_type == "application/json"
        payload = json.loads(contents[0].content)
        assert isinstance(payload, list)
        assert len(payload) > 0


def test_list_prompts():
    """list_prompts should return the three canonical prompts."""
    server = create_server()
    prompts = asyncio.run(server.list_prompts())
    names = {prompt.name for prompt in prompts}

    assert len(prompts) == 3
    assert names == {"validate_and_fix", "reduce_and_export", "analyze_system"}


def test_get_prompts():
    """get_prompt should return the step-by-step instruction message for each prompt."""
    server = create_server()
    prompt_args = {
        "validate_and_fix": {"system_path": "/tmp/system.json"},
        "reduce_and_export": {
            "system_path": "/tmp/system.json",
            "export_path": "/tmp/system.geojson",
        },
        "analyze_system": {"system_path": "/tmp/system.json"},
    }
    for name, arguments in prompt_args.items():
        result = asyncio.run(server.get_prompt(name, arguments))

        assert len(result.messages) == 1
        message = result.messages[0]
        assert message.role == "user"
        assert message.content.type == "text"
        assert "1." in message.content.text
