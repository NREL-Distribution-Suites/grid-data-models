from datetime import datetime
import pytest

from gdm.distribution.components import DistributionBus, DistributionLoad, DistributionSolar
from gdm.quantities import ReactivePower, Voltage
from gdm.distribution import DistributionSystem
from gdm.distribution.equipment import (
    PhaseCapacitorEquipment,
    LoadEquipment,
)
from gdm.tracked_changes import (
    filter_tracked_changes_by_name_and_date,
    apply_updates_to_system,
    TrackedChange,
    PropertyEdit,
)
from gdm.systems.component_utils import clone_components


def build_tracked_changes(
    system: DistributionSystem,
    addition_id: int,
) -> tuple[list[TrackedChange], int, int, int]:
    capacitor = next(system.get_components(PhaseCapacitorEquipment))

    load1, load2 = list(system.get_components(DistributionLoad))[:2]
    update_scenario = [
        TrackedChange(
            scenario_name="scenario_1",
            timestamp="2022-01-01 00:00:00",
            edits=[
                PropertyEdit(
                    component_id=capacitor.id,
                    name="rated_reactive_power",
                    value=ReactivePower(200, "kvar"),
                )
            ],
        ),
        TrackedChange(
            scenario_name="scenario_1",
            timestamp="2023-01-01 00:00:00",
            additions=[addition_id],
        ),
        TrackedChange(
            scenario_name="scenario_1",
            timestamp="2024-01-01 00:00:00",
            deletions=[load1.id],
        ),
        TrackedChange(
            scenario_name="scenario_2",
            timestamp="2025-01-01 00:00:00",
            deletions=[load2.id],
        ),
    ]
    return update_scenario, capacitor.id, load1.id, load2.id


def build_catalog() -> tuple[DistributionSystem, int]:
    catalog = DistributionSystem(auto_add_composed_components=True)
    load_equipment = LoadEquipment.example().model_copy(update={"name": "added_phase_load_model"})
    catalog.add_component(load_equipment)
    assert load_equipment.id is not None
    return catalog, load_equipment.id


def test_tracked_changes_by_date(distribution_system_with_single_time_series):
    system: DistributionSystem = distribution_system_with_single_time_series

    catalog, addition_id = build_catalog()
    tracked_changes, cap_id, load_1_id, load_2_id = build_tracked_changes(system, addition_id)
    system_date = datetime.strptime("2024-1-1", r"%Y-%m-%d")
    apply_updates_to_system(
        tracked_changes=tracked_changes, system=system, catalog=catalog, system_date=system_date
    )


def test_scenario_update(distribution_system_with_single_time_series):
    system: DistributionSystem = distribution_system_with_single_time_series
    catalog, addition_id = build_catalog()
    tracked_changes, cap_id, _, _ = build_tracked_changes(system, addition_id)
    with pytest.raises(ValueError):
        apply_updates_to_system(tracked_changes=tracked_changes, system=system, catalog=catalog)


def test_scenario_update_filter_by_scenario_name(distribution_system_with_single_time_series):
    system: DistributionSystem = distribution_system_with_single_time_series
    catalog, addition_id = build_catalog()
    tracked_changes, cap_id, _, _ = build_tracked_changes(system, addition_id)
    tracked_changes = filter_tracked_changes_by_name_and_date(
        tracked_changes, scenario_name="scenario_1"
    )
    updated_system = apply_updates_to_system(
        tracked_changes=tracked_changes, system=system, catalog=catalog
    )
    capacitor_new = updated_system.get_component_by_id(cap_id)

    assert capacitor_new.rated_reactive_power.to("kilovar").magnitude == 200.0


def test_scenario_update_filter_by_scenario_name_and_date(
    distribution_system_with_single_time_series,
):
    system: DistributionSystem = distribution_system_with_single_time_series
    catalog, addition_id = build_catalog()
    tracked_changes, cap_id, _, _ = build_tracked_changes(system, addition_id)
    tracked_changes = filter_tracked_changes_by_name_and_date(
        tracked_changes,
        scenario_name="scenario_1",
        timestamp=datetime.strptime("2022-1-1", "%Y-%m-%d"),
    )
    updated_system = apply_updates_to_system(
        tracked_changes=tracked_changes, system=system, catalog=catalog
    )
    capacitor = updated_system.get_component_by_id(cap_id)
    assert capacitor.rated_reactive_power.to("kilovar").magnitude == 200.0


def test_scenario_update_deletion_cascades_without_duplicate_child_failure():
    system = DistributionSystem(auto_add_composed_components=True)
    load = DistributionLoad.example()
    system.add_component(load)
    catalog = DistributionSystem(auto_add_composed_components=True)

    updated_system = apply_updates_to_system(
        [TrackedChange(scenario_name="scenario_1", deletions=[load.id])],
        system,
        catalog,
    )

    assert not updated_system.has_component(load)


def test_scenario_update_addition_rebinds_nested_component_to_system_instance():
    system = DistributionSystem(auto_add_composed_components=True)
    load = DistributionLoad.example()
    system.add_component(load)
    bus = load.bus

    catalog = DistributionSystem(auto_add_composed_components=True)
    catalog.add_component(
        DistributionBus.example().model_copy(update={"name": "catalog-offset-bus"})
    )
    solar = DistributionSolar.example()
    bus_copies, _ = clone_components([bus])
    solar.bus = bus_copies[0]
    catalog.add_component(solar)
    assert solar.id is not None
    assert bus.id is not None
    assert solar.bus.id != bus.id

    updated_system = apply_updates_to_system(
        [
            TrackedChange(
                scenario_name="scenario_1",
                additions=[solar.id],
                edits=[
                    PropertyEdit(
                        component_id=bus.id,
                        name="rated_voltage",
                        value=Voltage(999, "volt"),
                    )
                ],
            )
        ],
        system,
        catalog,
    )

    canonical_bus = updated_system.get_component_by_id(bus.id)
    new_solar = updated_system.get_component(DistributionSolar, solar.name)
    assert new_solar.bus is canonical_bus
    assert new_solar.bus.rated_voltage == Voltage(999, "volt")
