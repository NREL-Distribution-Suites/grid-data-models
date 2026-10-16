import pytest

from gdm.distribution import DistributionSystem
from gdm.distribution.components import (
    DistributionBus,
    DistributionFeeder,
    DistributionVoltageSource,
    GeometryBranch,
    MatrixImpedanceBranch,
)
from gdm.distribution.equipment import (
    CircuitBreakerEquipment,
    GeometryBranchEquipment,
    PowerTransformerEquipment,
)
from gdm.systems.distribution.components import DistributionTransformer
from gdm.systems.component_utils import clone_components
from gdm.systems.substation import (
    BusbarSection,
    CircuitBreaker,
    EquipmentState,
    FeederBoundary,
    PowerTransformer,
    SubstationSystem,
)


def test_distribution_system_with_timeseries(distribution_system_with_single_time_series):
    """Tests creation of sample distribution system with timeseries."""

    assert isinstance(distribution_system_with_single_time_series, DistributionSystem)


def test_geometry_conversion(distribution_system_with_single_time_series):
    """Tests creation of sample distribution system with timeseries."""

    sys = distribution_system_with_single_time_series
    assert len(list(sys.get_components(MatrixImpedanceBranch))) == 18
    assert len(list(sys.get_components(GeometryBranch))) == 0
    branch = sys.get_component(MatrixImpedanceBranch, "line_bus_8_bus_9")
    new_branch = GeometryBranch.example()
    new_branch.buses = branch.buses
    sys.remove_component(branch)
    sys.add_component(new_branch)
    assert len(list(sys.get_components(MatrixImpedanceBranch))) == 17
    assert len(list(sys.get_components(GeometryBranch))) == 1
    assert len(list(sys.get_components(GeometryBranchEquipment))) == 1
    sys.convert_geometry_to_matrix_representation()
    assert len(list(sys.get_components(MatrixImpedanceBranch))) == 18
    assert len(list(sys.get_components(GeometryBranch))) == 0
    assert len(list(sys.get_components(GeometryBranchEquipment))) == 0


def test_distribution_graph_includes_station_transformers_and_switches():
    system = DistributionSystem(name="expanded-station", auto_add_composed_components=True)
    transformer = PowerTransformer.example()
    station_bus = transformer.buses[0]
    source_bus = BusbarSection.example().model_copy(update={"name": "source-bus"})
    breaker = CircuitBreaker(
        name="source-breaker",
        buses=[source_bus, station_bus],
        equipment=CircuitBreakerEquipment.example(),
        state=EquipmentState.OPEN,
    )

    system.add_components(source_bus, transformer, breaker)
    graph = system.get_undirected_graph()

    assert {data["name"] for _, _, data in graph.edges(data=True)} == {
        "main-transformer-001",
        "source-breaker",
    }
    breaker_data = next(
        data for _, _, data in graph.edges(data=True) if data["name"] == breaker.name
    )
    assert breaker_data["is_switch"] is True
    assert breaker_data["is_closed"] is False


def test_replace_transformer_with_substation_replaces_abstract_edge():
    system = DistributionSystem(name="expanded-station", auto_add_composed_components=True)
    transformer = DistributionTransformer.example()
    source_bus, feeder_bus = transformer.buses
    station_terminal_buses, _ = clone_components([source_bus, feeder_bus])
    station_source_bus, station_feeder_bus = station_terminal_buses
    station_high_bus = BusbarSection(
        name="station-high-bus",
        rated_voltage=source_bus.rated_voltage,
        voltage_type=source_bus.voltage_type,
        phases=source_bus.phases,
    )
    station_low_bus = BusbarSection(
        name="station-low-bus",
        rated_voltage=feeder_bus.rated_voltage,
        voltage_type=feeder_bus.voltage_type,
        phases=feeder_bus.phases,
    )
    equipment = PowerTransformerEquipment(**transformer.equipment.model_dump())
    power_transformer = PowerTransformer(
        name="station-transformer",
        buses=[station_high_bus, station_low_bus],
        winding_phases=transformer.winding_phases,
        equipment=equipment,
    )
    high_side_breaker = CircuitBreaker(
        name="station-high-breaker",
        buses=[station_source_bus, station_high_bus],
        equipment=CircuitBreakerEquipment.example(),
        state=EquipmentState.CLOSED,
    )
    low_side_breaker = CircuitBreaker(
        name="station-low-breaker",
        buses=[station_low_bus, station_feeder_bus],
        equipment=CircuitBreakerEquipment.example(),
        state=EquipmentState.CLOSED,
    )
    voltage_source = DistributionVoltageSource.example().model_copy(update={"bus": source_bus})
    system.add_components(transformer, voltage_source)

    substation_system = SubstationSystem(name="station-detail", auto_add_composed_components=True)
    substation_system.add_components(
        station_high_bus,
        station_low_bus,
        high_side_breaker,
        power_transformer,
        low_side_breaker,
        FeederBoundary(
            name="feeder-boundary",
            feeder_id=transformer.feeder.name,
            bus=station_low_bus,
        ),
    )
    result = system.replace_transformer_with_substation(transformer, substation_system)

    assert isinstance(result, PowerTransformer)
    assert result is not power_transformer
    assert not system.has_component(transformer)
    assert system.has_component(result)
    assert {data["name"] for _, _, data in system.get_undirected_graph().edges(data=True)} == {
        "station-high-breaker",
        "station-transformer",
        "station-low-breaker",
    }

    system.get_component(CircuitBreaker, "station-low-breaker").state = EquipmentState.OPEN
    directed_graph = system.get_directed_graph()

    assert source_bus.name in directed_graph
    assert feeder_bus.name not in directed_graph


def test_replace_transformer_requires_matching_substation_feeder():
    system = DistributionSystem(name="expanded-station", auto_add_composed_components=True)
    transformer = DistributionTransformer.example()
    system.add_component(transformer)
    substation_system = SubstationSystem(name="station-detail", auto_add_composed_components=True)
    substation_system.add_component(
        FeederBoundary(
            name="other-feeder-boundary",
            feeder_id="other-feeder",
            bus=BusbarSection.example(),
        )
    )

    with pytest.raises(ValueError, match="matching feeder"):
        system.replace_transformer_with_substation(transformer, substation_system)

    assert system.has_component(transformer)


def test_substation_feeder_subsystem_retains_only_matching_outfeeds():
    system = DistributionSystem(name="distribution", auto_add_composed_components=True)
    transformer = DistributionTransformer.example()
    other_bus = DistributionBus.example().model_copy(
        update={
            "name": "other-feeder-bus",
            "feeder": DistributionFeeder(name="other-feeder"),
        }
    )
    system.add_components(transformer, other_bus)
    substation_system = SubstationSystem(name="station", auto_add_composed_components=True)
    substation_system.add_component(
        FeederBoundary(
            name="matching-boundary",
            feeder_id=transformer.feeder.name,
            bus=BusbarSection.example(),
        )
    )

    feeder_subsystem = system.get_substation_feeder_subsystem(substation_system)

    assert not feeder_subsystem.has_component(other_bus)
    assert all(
        component.feeder.name == transformer.feeder.name
        for component in feeder_subsystem.iter_all_components()
        if getattr(component, "feeder", None) is not None
    )


def test_get_subsystem_copies_components_and_preserves_time_series(
    distribution_system_with_single_time_series,
):
    system = distribution_system_with_single_time_series
    source_components = list(system.iter_all_components())
    bus_names = list(system.get_directed_graph().nodes)

    subsystem = system.get_subsystem(bus_names, name="network-copy", keep_time_series=True)

    subsystem_component_objects = {id(component) for component in subsystem.iter_all_components()}
    source_component = next(
        component
        for component in source_components
        if system.has_time_series(component)
        and (type(component), component.name)
        in {
            (type(subsystem_component), subsystem_component.name)
            for subsystem_component in subsystem.iter_all_components()
        }
    )
    subsystem_component = subsystem.get_component(type(source_component), source_component.name)

    assert id(source_component) not in subsystem_component_objects
    assert system.has_component(source_component)
    assert subsystem.has_time_series(subsystem_component)
    assert [
        metadata.name for metadata in subsystem.list_time_series_metadata(subsystem_component)
    ] == [metadata.name for metadata in system.list_time_series_metadata(source_component)]
