"""Tests for system merge operations."""

import pytest
from gdm.distribution import DistributionSystem
from gdm.distribution.components import DistributionBus, DistributionFeeder, DistributionSubstation
from gdm.distribution.enums import VoltageTypes
from gdm.mcp.exceptions import MergeConflictError
from gdm.mcp.operations.splitter import split_by_feeder
from gdm.quantities import Voltage
from gdm.mcp.operations.merger import merge_systems


def test_merge_two_systems(simple_system):
    """Test merging two systems."""
    # Create a completely separate second system with its own component IDs
    system2 = DistributionSystem(name="test_system_2", auto_add_composed_components=True)
    sub2 = DistributionSubstation(name="sub2", feeders=[])
    feeder2 = DistributionFeeder(name="feeder2")
    sub2.feeders.append(feeder2)
    bus3 = DistributionBus(
        name="bus3",
        phases=["A", "B", "C"],
        voltage_type=VoltageTypes.LINE_TO_LINE,
        rated_voltage=Voltage(12.47, "kV"),
        substation=sub2,
        feeder=feeder2,
    )
    system2.add_component(sub2)
    system2.add_component(bus3)

    systems = [simple_system, system2]
    merged_system, report = merge_systems(systems, name="merged_system", strict=True)

    assert report.success
    assert report.output_system_name == "merged_system"
    assert report.input_system_count == 2
    assert merged_system.name == "merged_system"
    # Should have components from both systems (more than just simple_system's 3 components)
    assert report.total_components_merged > 3


def test_merge_with_conflicts(simple_system):
    """Test that merge detects component-name conflicts across systems."""
    systems = [simple_system, simple_system]

    with pytest.raises(MergeConflictError) as error:
        merge_systems(systems, name="conflicted", strict=True)

    assert all(conflict["conflict_type"] == "name" for conflict in error.value.conflicts)


def test_merge_preserves_names(simple_system):
    """Test that merge preserves component structure."""
    # Create new system with different names
    system2 = DistributionSystem(name="system2", auto_add_composed_components=True)
    sub_copy = DistributionSubstation(name="sub1_copy", feeders=[])
    feeder_copy = DistributionFeeder(name="feeder1_copy")
    sub_copy.feeders.append(feeder_copy)
    bus1_copy = DistributionBus(
        name="bus1_copy",
        phases=["A", "B", "C"],
        voltage_type=VoltageTypes.LINE_TO_LINE,
        rated_voltage=Voltage(12.47, "kV"),
        substation=sub_copy,
        feeder=feeder_copy,
    )
    system2.add_component(sub_copy)
    system2.add_component(bus1_copy)

    systems = [simple_system, system2]
    merged_system, report = merge_systems(systems, name="merged", strict=True)

    # Check that both original and copy components exist
    component_names = {c.name for c in merged_system.iter_all_components()}
    assert "bus1" in component_names
    assert "bus1_copy" in component_names


def test_merge_copies_components_and_preserves_time_series(
    distribution_system_with_single_time_series,
):
    source = distribution_system_with_single_time_series
    source_components = list(source.iter_all_components())
    expected_timeseries_count = sum(
        len(source.list_time_series_metadata(component))
        for component in source_components
        if source.has_time_series(component)
    )

    merged, report = merge_systems([source], name="merged_with_profiles")

    assert report.timeseries_transferred == expected_timeseries_count
    merged_component_objects = {id(component) for component in merged.iter_all_components()}
    for component in source_components:
        assert source.has_component(component)
        assert id(component) not in merged_component_objects
        if not source.has_time_series(component):
            continue
        matching_components = list(
            merged.get_components(
                type(component), filter_func=lambda candidate: candidate.name == component.name
            )
        )
        assert len(matching_components) == 1
        merged_component = matching_components[0]
        assert merged_component is not component
        assert [
            metadata.name for metadata in merged.list_time_series_metadata(merged_component)
        ] == [metadata.name for metadata in source.list_time_series_metadata(component)]


def test_split_by_feeder_copies_components_and_preserves_time_series(
    distribution_system_with_single_time_series,
):
    source = distribution_system_with_single_time_series
    subsystems, report = split_by_feeder(source)

    assert report.success
    source_component = next(
        component
        for component in source.iter_all_components()
        if source.has_time_series(component)
    )
    feeder = getattr(source_component, "feeder", None)
    subsystem = subsystems[feeder.name if feeder is not None else "unassigned"]
    subsystem_component = subsystem.get_component(type(source_component), source_component.name)

    assert source.has_component(source_component)
    assert subsystem_component is not source_component
    assert subsystem.has_time_series(subsystem_component)
    assert [
        metadata.name for metadata in subsystem.list_time_series_metadata(subsystem_component)
    ] == [metadata.name for metadata in source.list_time_series_metadata(source_component)]
