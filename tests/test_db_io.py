import sqlite3
import os
from uuid import uuid4

import pytest
import psycopg
from infrasys.time_series_models import SingleTimeSeries

from gdm.distribution import CatalogSystem, DistributionSystem
from gdm.distribution.components import (
    DistributionBattery,
    DistributionBus,
    DistributionCapacitor,
    DistributionLoad,
    DistributionRegulator,
    DistributionSolar,
    DistributionTransformer,
    DistributionVoltageSource,
    GeometryBranch,
    MatrixImpedanceBranch,
    MatrixImpedanceFuse,
    MatrixImpedanceRecloser,
    MatrixImpedanceSwitch,
    SequenceImpedanceBranch,
)
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.controllers.distribution_inverter_controller import (
    InverterController,
    PeakShavingBaseLoadingControlSetting,
    VoltVarControlSetting,
)
from gdm.distribution.controllers.distribution_regulator_controller import RegulatorController
from gdm.distribution.controllers.distribution_recloser_controller import (
    DistributionRecloserController,
)
from gdm.distribution.equipment.battery_equipment import BatteryEquipment
from gdm.distribution.equipment.inverter_equipment import InverterEquipment
from gdm.distribution.enums import Phase
from gdm.distribution.equipment import LoadEquipment
from gdm.distribution.equipment.sequence_impedance_branch_equipment import (
    SequenceImpedanceBranchEquipment,
)
from gdm.distribution.equipment.matrix_impedance_switch_equipment import (
    MatrixImpedanceSwitchEquipment,
)
from gdm.distribution.equipment.geometry_branch_equipment import GeometryBranchEquipment
from gdm.distribution.equipment.matrix_impedance_fuse_equipment import MatrixImpedanceFuseEquipment
from gdm.distribution.equipment.matrix_impedance_recloser_equipment import (
    MatrixImpedanceRecloserEquipment,
)
from gdm.quantities import ActivePower, ReactivePower


def _postgres_dsn_or_skip() -> str:
    dsn = os.getenv("GDM_TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("Set GDM_TEST_POSTGRES_DSN to run PostgreSQL persistence tests.")
    return dsn


def test_distribution_system_to_db_from_db_round_trip(tmp_path, simple_distribution_system):
    system: DistributionSystem = simple_distribution_system
    db_path = tmp_path / "distribution.sqlite"

    system.to_db(db_path)
    loaded_system = DistributionSystem.from_db(db_path)

    initial_components = list(system.iter_all_components())
    loaded_components = list(loaded_system.iter_all_components())
    assert len(loaded_components) == len(initial_components)
    assert {component.uuid for component in loaded_components} == {
        component.uuid for component in initial_components
    }


def test_distribution_system_to_db_from_db_round_trip_with_sqlite_url(
    tmp_path, simple_distribution_system
):
    system: DistributionSystem = simple_distribution_system
    db_path = tmp_path / "distribution_url.sqlite"
    db_url = f"sqlite:///{db_path}"

    system.to_db(db_url=db_url)
    loaded_system = DistributionSystem.from_db(db_url=db_url)

    initial_components = list(system.iter_all_components())
    loaded_components = list(loaded_system.iter_all_components())
    assert len(loaded_components) == len(initial_components)
    assert {component.uuid for component in loaded_components} == {
        component.uuid for component in initial_components
    }


def test_distribution_system_to_db_replace_semantics(tmp_path, simple_distribution_system):
    system: DistributionSystem = simple_distribution_system
    db_path = tmp_path / "distribution.sqlite"
    system.to_db(db_path)

    modified_system = system.deepcopy()
    removed_component = next(iter(modified_system.get_components(DistributionLoad)))
    modified_system.remove_component(removed_component, cascade_down=False)
    modified_system.to_db(db_path, replace=True, initialize_schema=False)

    loaded_system = DistributionSystem.from_db(db_path)
    assert len(list(loaded_system.iter_all_components())) == len(
        list(modified_system.iter_all_components())
    )


def test_catalog_system_to_db_from_db_round_trip(tmp_path):
    catalog = CatalogSystem(auto_add_composed_components=True)
    catalog_equipment = LoadEquipment.example().model_copy(
        update={"uuid": uuid4(), "name": "catalog_load_equipment"}
    )
    catalog.add_component(catalog_equipment)

    db_path = tmp_path / "catalog.sqlite"
    catalog.to_db(db_path)
    loaded_catalog = CatalogSystem.from_db(db_path)

    loaded_equipment = loaded_catalog.get_component(LoadEquipment, name="catalog_load_equipment")
    assert loaded_equipment.uuid == catalog_equipment.uuid


def test_catalog_system_to_db_from_db_round_trip_with_sqlite_url(tmp_path):
    catalog = CatalogSystem(auto_add_composed_components=True)
    catalog_equipment = LoadEquipment.example().model_copy(
        update={"uuid": uuid4(), "name": "catalog_load_equipment_url"}
    )
    catalog.add_component(catalog_equipment)

    db_path = tmp_path / "catalog_url.sqlite"
    db_url = f"sqlite:///{db_path}"
    catalog.to_db(db_url=db_url)
    loaded_catalog = CatalogSystem.from_db(db_url=db_url)

    loaded_equipment = loaded_catalog.get_component(
        LoadEquipment, name="catalog_load_equipment_url"
    )
    assert loaded_equipment.uuid == catalog_equipment.uuid


def test_distribution_system_to_db_from_db_round_trip_with_postgres_dsn(
    simple_distribution_system,
):
    db_url = _postgres_dsn_or_skip()

    system: DistributionSystem = simple_distribution_system
    system.to_db(db_url=db_url, replace=True)
    loaded_system = DistributionSystem.from_db(db_url=db_url)

    initial_components = list(system.iter_all_components())
    loaded_components = list(loaded_system.iter_all_components())
    assert len(loaded_components) == len(initial_components)
    assert {component.uuid for component in loaded_components} == {
        component.uuid for component in initial_components
    }


def test_distribution_system_to_db_replace_semantics_with_postgres_dsn(
    simple_distribution_system,
):
    db_url = _postgres_dsn_or_skip()

    system: DistributionSystem = simple_distribution_system
    system.to_db(db_url=db_url, replace=True)

    modified_system = system.deepcopy()
    removed_component = next(iter(modified_system.get_components(DistributionLoad)))
    modified_system.remove_component(removed_component, cascade_down=False)
    modified_system.to_db(db_url=db_url, replace=True)

    loaded_system = DistributionSystem.from_db(db_url=db_url)
    assert len(list(loaded_system.iter_all_components())) == len(
        list(modified_system.iter_all_components())
    )


def test_catalog_system_to_db_from_db_round_trip_with_postgres_dsn():
    db_url = _postgres_dsn_or_skip()

    catalog = CatalogSystem(auto_add_composed_components=True)
    catalog_equipment = LoadEquipment.example().model_copy(
        update={"uuid": uuid4(), "name": "catalog_load_equipment_postgres"}
    )
    catalog.add_component(catalog_equipment)

    catalog.to_db(db_url=db_url, replace=True)
    loaded_catalog = CatalogSystem.from_db(db_url=db_url)

    loaded_equipment = loaded_catalog.get_component(
        LoadEquipment, name="catalog_load_equipment_postgres"
    )
    assert loaded_equipment.uuid == catalog_equipment.uuid


def test_distribution_system_from_db_prefer_normalized_with_postgres_dsn(
    simple_distribution_system,
):
    db_url = _postgres_dsn_or_skip()

    system: DistributionSystem = simple_distribution_system
    system.to_db(db_url=db_url, replace=True)

    loaded_system = DistributionSystem.from_db(db_url=db_url, prefer_normalized=True)

    expected_buses = list(system.get_components(DistributionBus))
    expected_feeders = {component.name for component in system.get_components(DistributionFeeder)}
    expected_substations = {
        component.name for component in system.get_components(DistributionSubstation)
    }
    expected_loads = list(system.get_components(DistributionLoad))

    loaded_buses = list(loaded_system.get_components(DistributionBus))
    loaded_feeders = list(loaded_system.get_components(DistributionFeeder))
    loaded_substations = list(loaded_system.get_components(DistributionSubstation))
    loaded_loads = list(loaded_system.get_components(DistributionLoad))

    assert len(loaded_buses) == len(expected_buses)
    assert len(loaded_feeders) == len(expected_feeders)
    assert len(loaded_substations) == len(expected_substations)
    assert len(loaded_loads) == len(expected_loads)

    assert {component.uuid for component in loaded_buses} == {
        component.uuid for component in expected_buses
    }
    assert {component.uuid for component in loaded_loads} == {
        component.uuid for component in expected_loads
    }


def test_distribution_system_from_db_prefer_normalized_attaches_time_series_with_postgres_dsn(
    distribution_system_with_single_timeseries,
):
    db_url = _postgres_dsn_or_skip()

    system: DistributionSystem = distribution_system_with_single_timeseries
    system.to_db(db_url=db_url, replace=True)

    original_load = next(iter(system.get_components(DistributionLoad)))
    loaded_system = DistributionSystem.from_db(db_url=db_url, prefer_normalized=True)
    loaded_load = loaded_system.get_component(DistributionLoad, name=original_load.name)

    assert loaded_system.has_time_series(loaded_load)

    original_metadata = system.list_time_series_metadata(original_load)
    loaded_metadata = loaded_system.list_time_series_metadata(loaded_load)
    assert len(loaded_metadata) == len(original_metadata)


def test_postgres_table_structure_matches_sqlite_after_distribution_write(
    simple_distribution_system,
):
    db_url = _postgres_dsn_or_skip()

    system: DistributionSystem = simple_distribution_system
    system.to_db(db_url=db_url, replace=True)

    psycopg_dsn = db_url.replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(psycopg_dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = 'distribution_buses'
                )
                """
            )
            row = cur.fetchone()

    assert row is not None
    assert row[0] is True


def test_distribution_system_from_db_prefer_normalized_topology(
    tmp_path, simple_distribution_system
):
    system: DistributionSystem = simple_distribution_system
    db_path = tmp_path / "distribution.sqlite"
    system.to_db(db_path)

    loaded_system = DistributionSystem.from_db(db_path, prefer_normalized=True)

    expected_buses = list(system.get_components(DistributionBus))
    expected_feeders = {component.name for component in system.get_components(DistributionFeeder)}
    expected_substations = {
        component.name for component in system.get_components(DistributionSubstation)
    }

    loaded_buses = list(loaded_system.get_components(DistributionBus))
    loaded_feeders = list(loaded_system.get_components(DistributionFeeder))
    loaded_substations = list(loaded_system.get_components(DistributionSubstation))
    loaded_loads = list(loaded_system.get_components(DistributionLoad))
    loaded_solar = list(loaded_system.get_components(DistributionSolar))
    loaded_capacitors = list(loaded_system.get_components(DistributionCapacitor))
    loaded_vsources = list(loaded_system.get_components(DistributionVoltageSource))
    loaded_transformers = list(loaded_system.get_components(DistributionTransformer))
    loaded_regulators = list(loaded_system.get_components(DistributionRegulator))
    loaded_matrix_branches = list(loaded_system.get_components(MatrixImpedanceBranch))

    expected_loads = list(system.get_components(DistributionLoad))
    expected_solar = list(system.get_components(DistributionSolar))
    expected_capacitors = list(system.get_components(DistributionCapacitor))
    expected_vsources = list(system.get_components(DistributionVoltageSource))
    expected_transformers = list(system.get_components(DistributionTransformer))
    expected_regulators = list(system.get_components(DistributionRegulator))
    expected_matrix_branches = list(system.get_components(MatrixImpedanceBranch))

    assert len(loaded_buses) == len(expected_buses)
    assert len(loaded_feeders) == len(expected_feeders)
    assert len(loaded_substations) == len(expected_substations)
    assert len(loaded_loads) == len(expected_loads)
    assert len(loaded_solar) == len(expected_solar)
    assert len(loaded_capacitors) == len(expected_capacitors)
    assert len(loaded_vsources) == len(expected_vsources)
    assert len(loaded_transformers) == len(expected_transformers)
    assert len(loaded_regulators) == len(expected_regulators)
    assert len(loaded_matrix_branches) == len(expected_matrix_branches)

    assert {component.uuid for component in loaded_buses} == {
        component.uuid for component in expected_buses
    }
    assert {component.uuid for component in loaded_loads} == {
        component.uuid for component in expected_loads
    }
    assert {component.uuid for component in loaded_solar} == {
        component.uuid for component in expected_solar
    }
    assert {component.uuid for component in loaded_capacitors} == {
        component.uuid for component in expected_capacitors
    }
    assert {component.uuid for component in loaded_vsources} == {
        component.uuid for component in expected_vsources
    }
    assert {component.uuid for component in loaded_transformers} == {
        component.uuid for component in expected_transformers
    }
    assert {component.uuid for component in loaded_regulators} == {
        component.uuid for component in expected_regulators
    }
    assert {component.uuid for component in loaded_matrix_branches} == {
        component.uuid for component in expected_matrix_branches
    }

    expected_solar_with_controller = {
        solar.uuid: solar for solar in expected_solar if solar.controller is not None
    }
    loaded_solar_by_uuid = {solar.uuid: solar for solar in loaded_solar}
    for solar_uuid, expected in expected_solar_with_controller.items():
        loaded = loaded_solar_by_uuid[solar_uuid]
        assert isinstance(loaded.controller, InverterController)
        assert type(loaded.controller.active_power_control) is type(
            expected.controller.active_power_control
        )
        assert type(loaded.controller.reactive_power_control) is type(
            expected.controller.reactive_power_control
        )

    loaded_regulator_by_uuid = {regulator.uuid: regulator for regulator in loaded_regulators}
    for expected_regulator in expected_regulators:
        loaded_regulator = loaded_regulator_by_uuid[expected_regulator.uuid]
        assert len(loaded_regulator.controllers) == len(expected_regulator.controllers)
        assert all(
            isinstance(controller, RegulatorController)
            for controller in loaded_regulator.controllers
        )


def test_distribution_system_from_db_prefer_normalized_with_battery(
    tmp_path, simple_distribution_system
):
    system: DistributionSystem = simple_distribution_system.deepcopy()

    bus = next(
        bus
        for bus in system.get_components(DistributionBus)
        if {Phase.A, Phase.B, Phase.C}.issubset(set(bus.phases))
    )

    battery = DistributionBattery(
        name="battery_test_component",
        bus=bus,
        substation=bus.substation,
        feeder=bus.feeder,
        phases=[Phase.A, Phase.B, Phase.C],
        active_power=ActivePower(150, "kilowatt"),
        reactive_power=ReactivePower(25, "kilovar"),
        equipment=BatteryEquipment.example().model_copy(update={"name": "battery_test_equipment"}),
        inverter=InverterEquipment.example().model_copy(update={"name": "battery_test_inverter"}),
        controller=InverterController(
            name="battery_test_controller",
            active_power_control=PeakShavingBaseLoadingControlSetting.example().model_copy(
                update={"name": "battery_test_peak_shave"}
            ),
            reactive_power_control=VoltVarControlSetting.example().model_copy(
                update={"name": "battery_test_volt_var"}
            ),
            prioritize_active_power=False,
            night_mode=True,
        ),
        in_service=True,
    )
    system.add_component(battery)

    db_path = tmp_path / "distribution_with_battery.sqlite"
    system.to_db(db_path)

    loaded_system = DistributionSystem.from_db(db_path, prefer_normalized=True)
    loaded_battery = loaded_system.get_component(
        DistributionBattery, name="battery_test_component"
    )

    assert loaded_battery.uuid == battery.uuid
    assert isinstance(loaded_battery.controller, InverterController)
    assert isinstance(
        loaded_battery.controller.active_power_control, PeakShavingBaseLoadingControlSetting
    )
    assert isinstance(loaded_battery.controller.reactive_power_control, VoltVarControlSetting)


def test_distribution_system_from_db_prefer_normalized_with_sequence_branch(
    tmp_path, simple_distribution_system
):
    system: DistributionSystem = simple_distribution_system.deepcopy()
    source_branch = next(iter(system.get_components(MatrixImpedanceBranch)))
    sequence_branch = SequenceImpedanceBranch(
        name="sequence_branch_test",
        buses=source_branch.buses,
        phases=source_branch.phases,
        length=source_branch.length,
        substation=source_branch.substation,
        feeder=source_branch.feeder,
        equipment=SequenceImpedanceBranchEquipment.example().model_copy(
            update={"name": "sequence_branch_equipment_test"}
        ),
        in_service=True,
    )
    system.add_component(sequence_branch)

    db_path = tmp_path / "distribution_with_sequence.sqlite"
    system.to_db(db_path)

    loaded_system = DistributionSystem.from_db(db_path, prefer_normalized=True)
    loaded_sequence_branch = loaded_system.get_component(
        SequenceImpedanceBranch,
        name="sequence_branch_test",
    )

    assert loaded_sequence_branch.uuid == sequence_branch.uuid
    assert loaded_sequence_branch.equipment.uuid == sequence_branch.equipment.uuid


def test_distribution_system_from_db_prefer_normalized_with_switch(
    tmp_path, simple_distribution_system
):
    system: DistributionSystem = simple_distribution_system.deepcopy()
    source_branch = next(iter(system.get_components(MatrixImpedanceBranch)))
    switch = MatrixImpedanceSwitch(
        name="switch_test_component",
        buses=source_branch.buses,
        phases=source_branch.phases,
        length=source_branch.length,
        substation=source_branch.substation,
        feeder=source_branch.feeder,
        is_closed=[True for _ in source_branch.phases],
        equipment=MatrixImpedanceSwitchEquipment.example().model_copy(
            update={"name": "switch_test_equipment"}
        ),
        in_service=True,
    )
    system.add_component(switch)

    db_path = tmp_path / "distribution_with_switch.sqlite"
    system.to_db(db_path)

    loaded_system = DistributionSystem.from_db(db_path, prefer_normalized=True)
    loaded_switch = loaded_system.get_component(
        MatrixImpedanceSwitch, name="switch_test_component"
    )

    assert loaded_switch.uuid == switch.uuid
    assert loaded_switch.equipment.uuid == switch.equipment.uuid
    assert loaded_switch.is_closed == switch.is_closed


def test_distribution_system_from_db_prefer_normalized_with_geometry_branch(
    tmp_path, simple_distribution_system
):
    system: DistributionSystem = simple_distribution_system.deepcopy()
    source_branch = next(iter(system.get_components(MatrixImpedanceBranch)))
    geometry_branch = GeometryBranch(
        name="geometry_branch_test",
        buses=source_branch.buses,
        phases=source_branch.phases,
        length=source_branch.length,
        substation=source_branch.substation,
        feeder=source_branch.feeder,
        equipment=GeometryBranchEquipment.example().model_copy(
            update={"name": "geometry_equipment_test"}
        ),
        in_service=True,
    )
    system.add_component(geometry_branch)

    db_path = tmp_path / "distribution_with_geometry.sqlite"
    system.to_db(db_path)

    loaded_system = DistributionSystem.from_db(db_path, prefer_normalized=True)
    loaded_geometry = loaded_system.get_component(GeometryBranch, name="geometry_branch_test")

    assert loaded_geometry.uuid == geometry_branch.uuid
    assert loaded_geometry.equipment.uuid == geometry_branch.equipment.uuid


def test_distribution_system_from_db_prefer_normalized_with_fuse(
    tmp_path, simple_distribution_system
):
    system: DistributionSystem = simple_distribution_system.deepcopy()
    source_branch = next(iter(system.get_components(MatrixImpedanceBranch)))
    fuse = MatrixImpedanceFuse(
        name="fuse_test_component",
        buses=source_branch.buses,
        phases=source_branch.phases,
        length=source_branch.length,
        substation=source_branch.substation,
        feeder=source_branch.feeder,
        is_closed=[True for _ in source_branch.phases],
        equipment=MatrixImpedanceFuseEquipment.example().model_copy(
            update={"name": "fuse_test_equipment"}
        ),
        in_service=True,
    )
    system.add_component(fuse)

    db_path = tmp_path / "distribution_with_fuse.sqlite"
    system.to_db(db_path)

    loaded_system = DistributionSystem.from_db(db_path, prefer_normalized=True)
    loaded_fuse = loaded_system.get_component(MatrixImpedanceFuse, name="fuse_test_component")

    assert loaded_fuse.uuid == fuse.uuid
    assert loaded_fuse.equipment.uuid == fuse.equipment.uuid
    assert loaded_fuse.equipment.tcc_curve.uuid == fuse.equipment.tcc_curve.uuid


def test_distribution_system_from_db_prefer_normalized_with_recloser(
    tmp_path, simple_distribution_system
):
    system: DistributionSystem = simple_distribution_system.deepcopy()
    source_branch = next(iter(system.get_components(MatrixImpedanceBranch)))
    recloser = MatrixImpedanceRecloser(
        name="recloser_test_component",
        buses=source_branch.buses,
        phases=source_branch.phases,
        length=source_branch.length,
        substation=source_branch.substation,
        feeder=source_branch.feeder,
        is_closed=[True for _ in source_branch.phases],
        equipment=MatrixImpedanceRecloserEquipment.example().model_copy(
            update={"name": "recloser_test_equipment"}
        ),
        controller=DistributionRecloserController.example().model_copy(
            update={"name": "recloser_test_controller"}
        ),
        in_service=True,
    )
    system.add_component(recloser)

    db_path = tmp_path / "distribution_with_recloser.sqlite"
    system.to_db(db_path)

    loaded_system = DistributionSystem.from_db(db_path, prefer_normalized=True)
    loaded_recloser = loaded_system.get_component(
        MatrixImpedanceRecloser,
        name="recloser_test_component",
    )

    assert loaded_recloser.uuid == recloser.uuid
    assert loaded_recloser.equipment.uuid == recloser.equipment.uuid
    assert loaded_recloser.controller.uuid == recloser.controller.uuid
    assert loaded_recloser.controller.equipment.uuid == recloser.controller.equipment.uuid


def test_distribution_system_to_db_writes_time_series_associations(
    tmp_path, distribution_system_with_single_timeseries
):
    system: DistributionSystem = distribution_system_with_single_timeseries
    db_path = tmp_path / "distribution_with_ts.sqlite"
    system.to_db(db_path)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) FROM time_series_associations").fetchone()
    assert row is not None
    assert row[0] > 0


def test_distribution_system_from_db_prefer_normalized_attaches_time_series(
    tmp_path, distribution_system_with_single_timeseries
):
    system: DistributionSystem = distribution_system_with_single_timeseries
    db_path = tmp_path / "distribution_with_ts.sqlite"
    system.to_db(db_path)

    original_load = next(iter(system.get_components(DistributionLoad)))
    loaded_system = DistributionSystem.from_db(db_path, prefer_normalized=True)
    loaded_load = loaded_system.get_component(DistributionLoad, name=original_load.name)

    assert loaded_system.has_time_series(loaded_load)

    original_metadata = system.list_time_series_metadata(original_load)
    loaded_metadata = loaded_system.list_time_series_metadata(loaded_load)
    assert len(loaded_metadata) == len(original_metadata)

    assert {metadata.name for metadata in loaded_metadata} == {
        metadata.name for metadata in original_metadata
    }

    for metadata in loaded_metadata:
        ts_data = loaded_system.get_time_series(
            loaded_load,
            metadata.name,
            SingleTimeSeries,
            **metadata.features,
        )
        assert ts_data is not None
