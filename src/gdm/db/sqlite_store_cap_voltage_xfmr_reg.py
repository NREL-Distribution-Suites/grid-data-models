"""Capacitor, voltage source, transformer, and regulator SQLite helpers."""

from __future__ import annotations

import sqlite3
from datetime import time

from infrasys.quantities import Angle, Time

from gdm.db.sqlite_store_identity import _fetch_component_uuid, _upsert_component_uuid_map
from gdm.distribution import DistributionSystem
from gdm.distribution.common.sequence_pair import SequencePair
from gdm.distribution.components import (
    DistributionBus,
    DistributionCapacitor,
    DistributionRegulator,
    DistributionTransformer,
    DistributionVoltageSource,
)
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.controllers.distribution_capacitor_controller import (
    ActivePowerCapacitorController,
    CurrentCapacitorController,
    DailyTimedCapacitorController,
    ReactivePowerCapacitorController,
    VoltageCapacitorController,
)
from gdm.distribution.controllers.distribution_regulator_controller import RegulatorController
from gdm.distribution.equipment.capacitor_equipment import CapacitorEquipment
from gdm.distribution.equipment.distribution_transformer_equipment import (
    DistributionTransformerEquipment,
    WindingEquipment,
)
from gdm.distribution.equipment.phase_capacitor_equipment import PhaseCapacitorEquipment
from gdm.distribution.equipment.phase_voltagesource_equipment import PhaseVoltageSourceEquipment
from gdm.distribution.equipment.voltagesource_equipment import VoltageSourceEquipment
from gdm.distribution.enums import ConnectionType, Phase, TransformerMounting, VoltageTypes
from gdm.quantities import (
    ActivePower,
    ApparentPower,
    Current,
    ReactivePower,
    Reactance,
    Resistance,
    Voltage,
)


def _write_distribution_capacitors(conn: sqlite3.Connection, system: DistributionSystem) -> None:
    bus_rows = conn.execute(
        "SELECT id, name, substation_id, feeder_id FROM distribution_buses"
    ).fetchall()
    bus_ref_by_name: dict[str, tuple[int, int, int]] = {
        name: (bus_id, substation_id, feeder_id)
        for bus_id, name, substation_id, feeder_id in bus_rows
    }

    phase_cap_equipment_id_by_name: dict[str, int] = {}
    cap_equipment_id_by_name: dict[str, int] = {}

    for capacitor in system.get_components(DistributionCapacitor):
        bus_ref = bus_ref_by_name.get(capacitor.bus.name)
        if bus_ref is None:
            raise ValueError(
                f"DistributionCapacitor '{capacitor.name}' references missing bus '{capacitor.bus.name}'"
            )

        bus_id, substation_id, feeder_id = bus_ref
        capacitor_equipment_id = _upsert_capacitor_equipment(
            conn,
            capacitor.equipment,
            phase_cap_equipment_id_by_name,
            cap_equipment_id_by_name,
        )

        cursor = conn.execute(
            """
            INSERT INTO distribution_capacitors(
                name,
                bus_id,
                substation_id,
                feeder_id,
                capacitor_equipment_id,
                in_service
            ) VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                capacitor.name,
                bus_id,
                substation_id,
                feeder_id,
                capacitor_equipment_id,
                1 if capacitor.in_service else 0,
            ),
        )
        capacitor_id = int(cursor.lastrowid)
        _upsert_component_uuid_map(conn, "distribution_capacitors", capacitor_id, capacitor.uuid)

        for position_index, phase in enumerate(capacitor.phases):
            conn.execute(
                "INSERT INTO distribution_capacitor_phases(capacitor_id, phase, position_index) VALUES(?, ?, ?)",
                (capacitor_id, phase.value, position_index),
            )

        _insert_capacitor_controllers(conn, capacitor_id, capacitor.controllers)


def _upsert_capacitor_equipment(
    conn: sqlite3.Connection,
    equipment: CapacitorEquipment,
    phase_cap_equipment_id_by_name: dict[str, int],
    cap_equipment_id_by_name: dict[str, int],
) -> int:
    cap_equipment_id = cap_equipment_id_by_name.get(equipment.name)
    if cap_equipment_id is None:
        existing = conn.execute(
            "SELECT id FROM capacitor_equipment WHERE name = ?",
            (equipment.name,),
        ).fetchone()
        if existing is None:
            cursor = conn.execute(
                """
                INSERT INTO capacitor_equipment(
                    name,
                    connection_type,
                    rated_voltage,
                    rated_voltage_unit,
                    voltage_type
                ) VALUES(?, ?, ?, ?, ?)
                """,
                (
                    equipment.name,
                    equipment.connection_type.value,
                    float(equipment.rated_voltage.magnitude),
                    str(equipment.rated_voltage.units),
                    equipment.voltage_type.value,
                ),
            )
            cap_equipment_id = int(cursor.lastrowid)
        else:
            cap_equipment_id = int(existing[0])

        cap_equipment_id_by_name[equipment.name] = cap_equipment_id
        _upsert_component_uuid_map(conn, "capacitor_equipment", cap_equipment_id, equipment.uuid)

        for position_index, phase_equipment in enumerate(equipment.phase_capacitors):
            phase_cap_id = _upsert_phase_capacitor_equipment(
                conn,
                phase_equipment,
                phase_cap_equipment_id_by_name,
            )
            conn.execute(
                """
                INSERT INTO capacitor_equipment_phases(
                    capacitor_equipment_id,
                    phase_capacitor_equipment_id,
                    position_index
                ) VALUES(?, ?, ?)
                """,
                (cap_equipment_id, phase_cap_id, position_index),
            )

    return cap_equipment_id


def _upsert_phase_capacitor_equipment(
    conn: sqlite3.Connection,
    phase_equipment: PhaseCapacitorEquipment,
    phase_cap_equipment_id_by_name: dict[str, int],
) -> int:
    phase_cap_id = phase_cap_equipment_id_by_name.get(phase_equipment.name)
    if phase_cap_id is None:
        existing = conn.execute(
            "SELECT id FROM phase_capacitor_equipment WHERE name = ?",
            (phase_equipment.name,),
        ).fetchone()
        if existing is None:
            cursor = conn.execute(
                """
                INSERT INTO phase_capacitor_equipment(
                    name,
                    resistance,
                    resistance_unit,
                    reactance,
                    reactance_unit,
                    rated_reactive_power,
                    rated_reactive_power_unit,
                    num_banks_on,
                    num_banks
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    phase_equipment.name,
                    float(phase_equipment.resistance.magnitude),
                    str(phase_equipment.resistance.units),
                    float(phase_equipment.reactance.magnitude),
                    str(phase_equipment.reactance.units),
                    float(phase_equipment.rated_reactive_power.magnitude),
                    str(phase_equipment.rated_reactive_power.units),
                    phase_equipment.num_banks_on,
                    phase_equipment.num_banks,
                ),
            )
            phase_cap_id = int(cursor.lastrowid)
        else:
            phase_cap_id = int(existing[0])

        phase_cap_equipment_id_by_name[phase_equipment.name] = phase_cap_id
        _upsert_component_uuid_map(
            conn, "phase_capacitor_equipment", phase_cap_id, phase_equipment.uuid
        )

    return phase_cap_id


def _insert_capacitor_controllers(
    conn: sqlite3.Connection,
    capacitor_id: int,
    controllers: list,
) -> None:
    for position_index, controller in enumerate(controllers):
        controller_type = None
        values = {
            "delay_on": None,
            "delay_on_unit": None,
            "delay_off": None,
            "delay_off_unit": None,
            "dead_time": None,
            "dead_time_unit": None,
            "on_voltage": None,
            "on_voltage_unit": None,
            "off_voltage": None,
            "off_voltage_unit": None,
            "pt_ratio": None,
            "on_active_power": None,
            "on_active_power_unit": None,
            "off_active_power": None,
            "off_active_power_unit": None,
            "on_reactive_power": None,
            "on_reactive_power_unit": None,
            "off_reactive_power": None,
            "off_reactive_power_unit": None,
            "on_current": None,
            "on_current_unit": None,
            "off_current": None,
            "off_current_unit": None,
            "ct_ratio": None,
            "on_time": None,
            "off_time": None,
        }

        if controller.delay_on is not None:
            values["delay_on"] = float(controller.delay_on.magnitude)
            values["delay_on_unit"] = str(controller.delay_on.units)
        if controller.delay_off is not None:
            values["delay_off"] = float(controller.delay_off.magnitude)
            values["delay_off_unit"] = str(controller.delay_off.units)
        if controller.dead_time is not None:
            values["dead_time"] = float(controller.dead_time.magnitude)
            values["dead_time_unit"] = str(controller.dead_time.units)

        if isinstance(controller, VoltageCapacitorController):
            controller_type = "VOLTAGE"
            values["on_voltage"] = float(controller.on_voltage.magnitude)
            values["on_voltage_unit"] = str(controller.on_voltage.units)
            values["off_voltage"] = float(controller.off_voltage.magnitude)
            values["off_voltage_unit"] = str(controller.off_voltage.units)
            values["pt_ratio"] = controller.pt_ratio
        elif isinstance(controller, ActivePowerCapacitorController):
            controller_type = "ACTIVE_POWER"
            values["on_active_power"] = float(controller.on_power.magnitude)
            values["on_active_power_unit"] = str(controller.on_power.units)
            values["off_active_power"] = float(controller.off_power.magnitude)
            values["off_active_power_unit"] = str(controller.off_power.units)
        elif isinstance(controller, ReactivePowerCapacitorController):
            controller_type = "REACTIVE_POWER"
            values["on_reactive_power"] = float(controller.on_power.magnitude)
            values["on_reactive_power_unit"] = str(controller.on_power.units)
            values["off_reactive_power"] = float(controller.off_power.magnitude)
            values["off_reactive_power_unit"] = str(controller.off_power.units)
        elif isinstance(controller, CurrentCapacitorController):
            controller_type = "CURRENT"
            values["on_current"] = float(controller.on_current.magnitude)
            values["on_current_unit"] = str(controller.on_current.units)
            values["off_current"] = float(controller.off_current.magnitude)
            values["off_current_unit"] = str(controller.off_current.units)
            values["ct_ratio"] = controller.ct_ratio
        elif isinstance(controller, DailyTimedCapacitorController):
            controller_type = "DAILY_TIMED"
            values["on_time"] = controller.on_time.strftime("%H:%M:%S")
            values["off_time"] = controller.off_time.strftime("%H:%M:%S")
        else:
            continue

        cursor = conn.execute(
            """
            INSERT INTO capacitor_controllers(
                capacitor_id,
                position_index,
                name,
                controller_type,
                delay_on,
                delay_on_unit,
                delay_off,
                delay_off_unit,
                dead_time,
                dead_time_unit,
                on_voltage,
                on_voltage_unit,
                off_voltage,
                off_voltage_unit,
                pt_ratio,
                on_active_power,
                on_active_power_unit,
                off_active_power,
                off_active_power_unit,
                on_reactive_power,
                on_reactive_power_unit,
                off_reactive_power,
                off_reactive_power_unit,
                on_current,
                on_current_unit,
                off_current,
                off_current_unit,
                ct_ratio,
                on_time,
                off_time
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                capacitor_id,
                position_index,
                controller.name,
                controller_type,
                values["delay_on"],
                values["delay_on_unit"],
                values["delay_off"],
                values["delay_off_unit"],
                values["dead_time"],
                values["dead_time_unit"],
                values["on_voltage"],
                values["on_voltage_unit"],
                values["off_voltage"],
                values["off_voltage_unit"],
                values["pt_ratio"],
                values["on_active_power"],
                values["on_active_power_unit"],
                values["off_active_power"],
                values["off_active_power_unit"],
                values["on_reactive_power"],
                values["on_reactive_power_unit"],
                values["off_reactive_power"],
                values["off_reactive_power_unit"],
                values["on_current"],
                values["on_current_unit"],
                values["off_current"],
                values["off_current_unit"],
                values["ct_ratio"],
                values["on_time"],
                values["off_time"],
            ),
        )
        controller_id = int(cursor.lastrowid)
        _upsert_component_uuid_map(conn, "capacitor_controllers", controller_id, controller.uuid)


def _write_distribution_voltage_sources(
    conn: sqlite3.Connection, system: DistributionSystem
) -> None:
    bus_rows = conn.execute(
        "SELECT id, name, substation_id, feeder_id FROM distribution_buses"
    ).fetchall()
    bus_ref_by_name: dict[str, tuple[int, int, int]] = {
        name: (bus_id, substation_id, feeder_id)
        for bus_id, name, substation_id, feeder_id in bus_rows
    }

    phase_vs_equipment_id_by_name: dict[str, int] = {}
    vs_equipment_id_by_name: dict[str, int] = {}

    for vsource in system.get_components(DistributionVoltageSource):
        bus_ref = bus_ref_by_name.get(vsource.bus.name)
        if bus_ref is None:
            raise ValueError(
                f"DistributionVoltageSource '{vsource.name}' references missing bus '{vsource.bus.name}'"
            )
        bus_id, substation_id, feeder_id = bus_ref

        vs_equipment_id = _upsert_voltage_source_equipment(
            conn,
            vsource.equipment,
            phase_vs_equipment_id_by_name,
            vs_equipment_id_by_name,
        )

        cursor = conn.execute(
            """
            INSERT INTO distribution_voltage_sources(
                name,
                bus_id,
                substation_id,
                feeder_id,
                voltage_source_equipment_id,
                in_service
            ) VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                vsource.name,
                bus_id,
                substation_id,
                feeder_id,
                vs_equipment_id,
                1 if vsource.in_service else 0,
            ),
        )
        vsource_id = int(cursor.lastrowid)
        _upsert_component_uuid_map(
            conn,
            "distribution_voltage_sources",
            vsource_id,
            vsource.uuid,
        )

        for position_index, phase in enumerate(vsource.phases):
            conn.execute(
                "INSERT INTO distribution_voltage_source_phases(vsource_id, phase, position_index) VALUES(?, ?, ?)",
                (vsource_id, phase.value, position_index),
            )


def _upsert_voltage_source_equipment(
    conn: sqlite3.Connection,
    equipment: VoltageSourceEquipment,
    phase_vs_equipment_id_by_name: dict[str, int],
    vs_equipment_id_by_name: dict[str, int],
) -> int:
    vs_equipment_id = vs_equipment_id_by_name.get(equipment.name)
    if vs_equipment_id is None:
        existing = conn.execute(
            "SELECT id FROM voltage_source_equipment WHERE name = ?",
            (equipment.name,),
        ).fetchone()
        if existing is None:
            cursor = conn.execute(
                "INSERT INTO voltage_source_equipment(name) VALUES(?)",
                (equipment.name,),
            )
            vs_equipment_id = int(cursor.lastrowid)
        else:
            vs_equipment_id = int(existing[0])
        vs_equipment_id_by_name[equipment.name] = vs_equipment_id
        _upsert_component_uuid_map(
            conn, "voltage_source_equipment", vs_equipment_id, equipment.uuid
        )

        for position_index, source in enumerate(equipment.sources):
            phase_source_id = _upsert_phase_voltage_source_equipment(
                conn,
                source,
                phase_vs_equipment_id_by_name,
            )
            conn.execute(
                """
                INSERT INTO voltage_source_phases(
                    voltage_source_equipment_id,
                    phase_source_equipment_id,
                    position_index
                ) VALUES(?, ?, ?)
                """,
                (vs_equipment_id, phase_source_id, position_index),
            )

    return vs_equipment_id


def _upsert_phase_voltage_source_equipment(
    conn: sqlite3.Connection,
    source: PhaseVoltageSourceEquipment,
    phase_vs_equipment_id_by_name: dict[str, int],
) -> int:
    phase_source_id = phase_vs_equipment_id_by_name.get(source.name)
    if phase_source_id is None:
        existing = conn.execute(
            "SELECT id FROM phase_voltage_source_equipment WHERE name = ?",
            (source.name,),
        ).fetchone()
        if existing is None:
            cursor = conn.execute(
                """
                INSERT INTO phase_voltage_source_equipment(
                    name,
                    r0,
                    r0_unit,
                    r1,
                    r1_unit,
                    x0,
                    x0_unit,
                    x1,
                    x1_unit,
                    voltage,
                    voltage_unit,
                    voltage_type,
                    angle,
                    angle_unit
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source.name,
                    float(source.r0.magnitude),
                    str(source.r0.units),
                    float(source.r1.magnitude),
                    str(source.r1.units),
                    float(source.x0.magnitude),
                    str(source.x0.units),
                    float(source.x1.magnitude),
                    str(source.x1.units),
                    float(source.voltage.magnitude),
                    str(source.voltage.units),
                    source.voltage_type.value,
                    float(source.angle.magnitude),
                    str(source.angle.units),
                ),
            )
            phase_source_id = int(cursor.lastrowid)
        else:
            phase_source_id = int(existing[0])
        phase_vs_equipment_id_by_name[source.name] = phase_source_id
        _upsert_component_uuid_map(
            conn,
            "phase_voltage_source_equipment",
            phase_source_id,
            source.uuid,
        )

    return phase_source_id


def _write_distribution_transformers(conn: sqlite3.Connection, system: DistributionSystem) -> None:
    bus_rows = conn.execute(
        "SELECT id, name, substation_id, feeder_id FROM distribution_buses"
    ).fetchall()
    bus_id_by_name: dict[str, int] = {name: bus_id for bus_id, name, _, _ in bus_rows}

    transformer_equipment_id_by_name: dict[str, int] = {}

    for transformer in system.get_components(DistributionTransformer):
        transformer_substation = transformer.substation
        transformer_feeder = transformer.feeder
        if (transformer_substation is None or transformer_feeder is None) and transformer.buses:
            fallback_bus = transformer.buses[0]
            transformer_substation = transformer_substation or fallback_bus.substation
            transformer_feeder = transformer_feeder or fallback_bus.feeder
        if transformer_substation is None or transformer_feeder is None:
            raise ValueError(
                f"DistributionTransformer '{transformer.name}' must have substation and feeder"
            )

        substation_row = conn.execute(
            "SELECT id FROM distribution_substations WHERE name = ?",
            (transformer_substation.name,),
        ).fetchone()
        feeder_row = conn.execute(
            "SELECT id FROM distribution_feeders WHERE name = ?",
            (transformer_feeder.name,),
        ).fetchone()
        if substation_row is None or feeder_row is None:
            raise ValueError(
                f"DistributionTransformer '{transformer.name}' references missing substation/feeder"
            )
        substation_id = int(substation_row[0])
        feeder_id = int(feeder_row[0])

        equipment_id = _upsert_distribution_transformer_equipment(
            conn,
            transformer.equipment,
            transformer_equipment_id_by_name,
        )

        cursor = conn.execute(
            """
            INSERT INTO distribution_transformers(
                name,
                substation_id,
                feeder_id,
                equipment_id,
                in_service
            ) VALUES(?, ?, ?, ?, ?)
            """,
            (
                transformer.name,
                substation_id,
                feeder_id,
                equipment_id,
                1 if transformer.in_service else 0,
            ),
        )
        transformer_id = int(cursor.lastrowid)
        _upsert_component_uuid_map(
            conn,
            "distribution_transformers",
            transformer_id,
            transformer.uuid,
        )

        for winding_index, bus in enumerate(transformer.buses):
            bus_id = bus_id_by_name.get(bus.name)
            if bus_id is None:
                raise ValueError(
                    f"DistributionTransformer '{transformer.name}' references unknown bus '{bus.name}'"
                )
            conn.execute(
                "INSERT INTO transformer_winding_buses(transformer_id, winding_index, bus_id) VALUES(?, ?, ?)",
                (transformer_id, winding_index, bus_id),
            )

        for winding_index, phases in enumerate(transformer.winding_phases):
            for phase_index, phase in enumerate(phases):
                conn.execute(
                    """
                    INSERT INTO transformer_winding_phases(
                        transformer_id,
                        winding_index,
                        phase,
                        phase_index
                    ) VALUES(?, ?, ?, ?)
                    """,
                    (transformer_id, winding_index, phase.value, phase_index),
                )


def _upsert_distribution_transformer_equipment(
    conn: sqlite3.Connection,
    equipment: DistributionTransformerEquipment,
    transformer_equipment_id_by_name: dict[str, int],
) -> int:
    equipment_id = transformer_equipment_id_by_name.get(equipment.name)
    if equipment_id is None:
        existing = conn.execute(
            "SELECT id FROM distribution_transformer_equipment WHERE name = ?",
            (equipment.name,),
        ).fetchone()
        if existing is None:
            cursor = conn.execute(
                """
                INSERT INTO distribution_transformer_equipment(
                    name,
                    mounting,
                    pct_no_load_loss,
                    pct_full_load_loss,
                    is_center_tapped
                ) VALUES(?, ?, ?, ?, ?)
                """,
                (
                    equipment.name,
                    equipment.mounting.value,
                    equipment.pct_no_load_loss,
                    equipment.pct_full_load_loss,
                    1 if equipment.is_center_tapped else 0,
                ),
            )
            equipment_id = int(cursor.lastrowid)
        else:
            equipment_id = int(existing[0])

        transformer_equipment_id_by_name[equipment.name] = equipment_id
        _upsert_component_uuid_map(
            conn,
            "distribution_transformer_equipment",
            equipment_id,
            equipment.uuid,
        )

        for winding_index, winding in enumerate(equipment.windings):
            winding_cursor = conn.execute(
                """
                INSERT INTO winding_equipment(
                    name,
                    transformer_equipment_id,
                    winding_index,
                    resistance,
                    is_grounded,
                    rated_voltage,
                    rated_voltage_unit,
                    voltage_type,
                    rated_power,
                    rated_power_unit,
                    num_phases,
                    connection_type,
                    total_taps,
                    min_tap_pu,
                    max_tap_pu
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    winding.name,
                    equipment_id,
                    winding_index,
                    winding.resistance,
                    1 if winding.is_grounded else 0,
                    float(winding.rated_voltage.magnitude),
                    str(winding.rated_voltage.units),
                    winding.voltage_type.value,
                    float(winding.rated_power.magnitude),
                    str(winding.rated_power.units),
                    winding.num_phases,
                    winding.connection_type.value,
                    winding.total_taps,
                    winding.min_tap_pu,
                    winding.max_tap_pu,
                ),
            )
            winding_id = int(winding_cursor.lastrowid)
            _upsert_component_uuid_map(conn, "winding_equipment", winding_id, winding.uuid)

            for position_index, tap in enumerate(winding.tap_positions):
                conn.execute(
                    "INSERT INTO winding_tap_positions(winding_id, position_index, tap_value) VALUES(?, ?, ?)",
                    (winding_id, position_index, tap),
                )

        for sequence_index, (pair, reactance) in enumerate(
            zip(equipment.coupling_sequences, equipment.winding_reactances)
        ):
            conn.execute(
                """
                INSERT INTO transformer_coupling_sequences(
                    transformer_equipment_id,
                    sequence_index,
                    from_winding_index,
                    to_winding_index,
                    reactance,
                    reactance_unit
                ) VALUES(?, ?, ?, ?, ?, ?)
                """,
                (
                    equipment_id,
                    sequence_index,
                    pair.from_index,
                    pair.to_index,
                    reactance,
                    "percent",
                ),
            )

    return equipment_id


def _write_distribution_regulators(conn: sqlite3.Connection, system: DistributionSystem) -> None:
    bus_rows = conn.execute(
        "SELECT id, name, substation_id, feeder_id FROM distribution_buses"
    ).fetchall()
    bus_id_by_name: dict[str, int] = {name: bus_id for bus_id, name, _, _ in bus_rows}

    transformer_equipment_id_by_name: dict[str, int] = {}

    for regulator in system.get_components(DistributionRegulator):
        regulator_substation = regulator.substation
        regulator_feeder = regulator.feeder
        if (regulator_substation is None or regulator_feeder is None) and regulator.buses:
            fallback_bus = regulator.buses[0]
            regulator_substation = regulator_substation or fallback_bus.substation
            regulator_feeder = regulator_feeder or fallback_bus.feeder
        if regulator_substation is None or regulator_feeder is None:
            raise ValueError(
                f"DistributionRegulator '{regulator.name}' must have substation and feeder"
            )

        substation_row = conn.execute(
            "SELECT id FROM distribution_substations WHERE name = ?",
            (regulator_substation.name,),
        ).fetchone()
        feeder_row = conn.execute(
            "SELECT id FROM distribution_feeders WHERE name = ?",
            (regulator_feeder.name,),
        ).fetchone()
        if substation_row is None or feeder_row is None:
            raise ValueError(
                f"DistributionRegulator '{regulator.name}' references missing substation/feeder"
            )
        substation_id = int(substation_row[0])
        feeder_id = int(feeder_row[0])

        equipment_id = _upsert_distribution_transformer_equipment(
            conn,
            regulator.equipment,
            transformer_equipment_id_by_name,
        )

        cursor = conn.execute(
            """
            INSERT INTO distribution_regulators(
                name,
                substation_id,
                feeder_id,
                equipment_id,
                in_service
            ) VALUES(?, ?, ?, ?, ?)
            """,
            (
                regulator.name,
                substation_id,
                feeder_id,
                equipment_id,
                1 if regulator.in_service else 0,
            ),
        )
        regulator_id = int(cursor.lastrowid)
        _upsert_component_uuid_map(conn, "distribution_regulators", regulator_id, regulator.uuid)

        for winding_index, bus in enumerate(regulator.buses):
            bus_id = bus_id_by_name.get(bus.name)
            if bus_id is None:
                raise ValueError(
                    f"DistributionRegulator '{regulator.name}' references unknown bus '{bus.name}'"
                )
            conn.execute(
                "INSERT INTO regulator_winding_buses(regulator_id, winding_index, bus_id) VALUES(?, ?, ?)",
                (regulator_id, winding_index, bus_id),
            )

        for winding_index, phases in enumerate(regulator.winding_phases):
            for phase_index, phase in enumerate(phases):
                conn.execute(
                    """
                    INSERT INTO regulator_winding_phases(
                        regulator_id,
                        winding_index,
                        phase,
                        phase_index
                    ) VALUES(?, ?, ?, ?)
                    """,
                    (regulator_id, winding_index, phase.value, phase_index),
                )

        for position_index, controller in enumerate(regulator.controllers):
            controlled_bus_id = bus_id_by_name.get(controller.controlled_bus.name)
            if controlled_bus_id is None:
                raise ValueError(
                    f"RegulatorController '{controller.name}' references unknown bus '{controller.controlled_bus.name}'"
                )
            cursor = conn.execute(
                """
                INSERT INTO regulator_controllers(
                    regulator_id,
                    position_index,
                    name,
                    delay,
                    delay_unit,
                    v_setpoint,
                    v_setpoint_unit,
                    min_v_limit,
                    min_v_limit_unit,
                    max_v_limit,
                    max_v_limit_unit,
                    pt_ratio,
                    use_ldc,
                    is_reversible,
                    ldc_R,
                    ldc_R_unit,
                    ldc_X,
                    ldc_X_unit,
                    ct_primary,
                    ct_primary_unit,
                    max_step,
                    bandwidth,
                    bandwidth_unit,
                    controlled_bus_id,
                    controlled_phase
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    regulator_id,
                    position_index,
                    controller.name,
                    float(controller.delay.magnitude) if controller.delay is not None else None,
                    str(controller.delay.units) if controller.delay is not None else None,
                    float(controller.v_setpoint.magnitude),
                    str(controller.v_setpoint.units),
                    float(controller.min_v_limit.magnitude),
                    str(controller.min_v_limit.units),
                    float(controller.max_v_limit.magnitude),
                    str(controller.max_v_limit.units),
                    controller.pt_ratio,
                    1 if controller.use_ldc else 0,
                    1 if controller.is_reversible else 0,
                    float(controller.ldc_R.magnitude) if controller.ldc_R is not None else None,
                    str(controller.ldc_R.units) if controller.ldc_R is not None else None,
                    float(controller.ldc_X.magnitude) if controller.ldc_X is not None else None,
                    str(controller.ldc_X.units) if controller.ldc_X is not None else None,
                    float(controller.ct_primary.magnitude)
                    if controller.ct_primary is not None
                    else None,
                    str(controller.ct_primary.units)
                    if controller.ct_primary is not None
                    else None,
                    controller.max_step,
                    float(controller.bandwidth.magnitude),
                    str(controller.bandwidth.units),
                    controlled_bus_id,
                    controller.controlled_phase.value,
                ),
            )
            controller_id = int(cursor.lastrowid)
            _upsert_component_uuid_map(
                conn, "regulator_controllers", controller_id, controller.uuid
            )


def _load_or_cache_capacitor_equipment(
    conn: sqlite3.Connection,
    capacitor_equipment_id: int,
    equipment_cache: dict[int, CapacitorEquipment],
    phase_equipment_cache: dict[int, PhaseCapacitorEquipment],
) -> CapacitorEquipment:
    """Load CapacitorEquipment from DB (with caching) for a given equipment id."""
    equipment = equipment_cache.get(capacitor_equipment_id)
    if equipment is not None:
        return equipment

    equipment_row = conn.execute(
        """
        SELECT name, connection_type, rated_voltage, rated_voltage_unit, voltage_type
        FROM capacitor_equipment
        WHERE id = ?
        """,
        (capacitor_equipment_id,),
    ).fetchone()
    if equipment_row is None:
        raise ValueError(f"capacitor_equipment_id={capacitor_equipment_id} not found")
    (
        equipment_name,
        connection_type,
        rated_voltage,
        rated_voltage_unit,
        voltage_type,
    ) = equipment_row

    phase_links = conn.execute(
        """
        SELECT phase_capacitor_equipment_id
        FROM capacitor_equipment_phases
        WHERE capacitor_equipment_id = ?
        ORDER BY position_index
        """,
        (capacitor_equipment_id,),
    ).fetchall()
    phase_caps: list[PhaseCapacitorEquipment] = []
    for (phase_cap_id,) in phase_links:
        phase_cap = phase_equipment_cache.get(phase_cap_id)
        if phase_cap is None:
            phase_row = conn.execute(
                """
                SELECT
                    name,
                    resistance,
                    resistance_unit,
                    reactance,
                    reactance_unit,
                    rated_reactive_power,
                    rated_reactive_power_unit,
                    num_banks_on,
                    num_banks
                FROM phase_capacitor_equipment
                WHERE id = ?
                """,
                (phase_cap_id,),
            ).fetchone()
            if phase_row is None:
                raise ValueError(f"phase_capacitor_equipment_id={phase_cap_id} not found")
            (
                phase_name,
                resistance,
                resistance_unit,
                reactance,
                reactance_unit,
                rated_reactive_power,
                rated_reactive_power_unit,
                num_banks_on,
                num_banks,
            ) = phase_row
            phase_cap = PhaseCapacitorEquipment(
                name=phase_name,
                resistance=Resistance(resistance, resistance_unit),
                reactance=Reactance(reactance, reactance_unit),
                rated_reactive_power=ReactivePower(
                    rated_reactive_power, rated_reactive_power_unit
                ),
                num_banks_on=num_banks_on,
                num_banks=num_banks,
            )
            phase_cap_uuid = _fetch_component_uuid(
                conn,
                "phase_capacitor_equipment",
                phase_cap_id,
            )
            if phase_cap_uuid is not None:
                phase_cap = phase_cap.model_copy(update={"uuid": phase_cap_uuid})
            phase_equipment_cache[phase_cap_id] = phase_cap
        phase_caps.append(phase_cap)

    equipment = CapacitorEquipment(
        name=equipment_name,
        phase_capacitors=phase_caps,
        connection_type=ConnectionType(connection_type),
        rated_voltage=Voltage(rated_voltage, rated_voltage_unit),
        voltage_type=VoltageTypes(voltage_type),
    )
    equipment_uuid = _fetch_component_uuid(conn, "capacitor_equipment", capacitor_equipment_id)
    if equipment_uuid is not None:
        equipment = equipment.model_copy(update={"uuid": equipment_uuid})
    equipment_cache[capacitor_equipment_id] = equipment
    return equipment


def _build_capacitor_controller(conn: sqlite3.Connection, row: tuple) -> object | None:
    """Build a single capacitor controller from a DB row, or return None."""
    (
        controller_id,
        name,
        controller_type,
        delay_on,
        delay_on_unit,
        delay_off,
        delay_off_unit,
        dead_time,
        dead_time_unit,
        on_voltage,
        on_voltage_unit,
        off_voltage,
        off_voltage_unit,
        pt_ratio,
        on_active_power,
        on_active_power_unit,
        off_active_power,
        off_active_power_unit,
        on_reactive_power,
        on_reactive_power_unit,
        off_reactive_power,
        off_reactive_power_unit,
        on_current,
        on_current_unit,
        off_current,
        off_current_unit,
        ct_ratio,
        on_time,
        off_time,
    ) = row

    common = {
        "name": name,
        "delay_on": Time(delay_on, delay_on_unit)
        if delay_on is not None and delay_on_unit is not None
        else None,
        "delay_off": Time(delay_off, delay_off_unit)
        if delay_off is not None and delay_off_unit is not None
        else None,
        "dead_time": Time(dead_time, dead_time_unit)
        if dead_time is not None and dead_time_unit is not None
        else None,
    }
    controller = None
    if controller_type == "VOLTAGE":
        controller = VoltageCapacitorController(
            **common,
            on_voltage=Voltage(on_voltage, on_voltage_unit),
            off_voltage=Voltage(off_voltage, off_voltage_unit),
            pt_ratio=pt_ratio,
        )
    elif controller_type == "ACTIVE_POWER":
        controller = ActivePowerCapacitorController(
            **common,
            on_power=ActivePower(on_active_power, on_active_power_unit),
            off_power=ActivePower(off_active_power, off_active_power_unit),
        )
    elif controller_type == "REACTIVE_POWER":
        controller = ReactivePowerCapacitorController(
            **common,
            on_power=ReactivePower(on_reactive_power, on_reactive_power_unit),
            off_power=ReactivePower(off_reactive_power, off_reactive_power_unit),
        )
    elif controller_type == "CURRENT":
        controller = CurrentCapacitorController(
            **common,
            on_current=Current(on_current, on_current_unit),
            off_current=Current(off_current, off_current_unit),
            ct_ratio=ct_ratio,
        )
    elif controller_type == "DAILY_TIMED":
        controller = DailyTimedCapacitorController(
            **common,
            on_time=time.fromisoformat(on_time),
            off_time=time.fromisoformat(off_time),
        )

    if controller is not None:
        controller_uuid = _fetch_component_uuid(conn, "capacitor_controllers", controller_id)
        if controller_uuid is not None:
            controller = controller.model_copy(update={"uuid": controller_uuid})
    return controller


def _load_distribution_capacitors_from_normalized(
    conn: sqlite3.Connection,
    system: DistributionSystem,
    buses_by_id: dict[int, DistributionBus],
    substations_by_id: dict[int, DistributionSubstation],
    feeders_by_id: dict[int, DistributionFeeder],
) -> None:
    capacitor_rows = conn.execute(
        """
        SELECT
            id,
            name,
            bus_id,
            substation_id,
            feeder_id,
            capacitor_equipment_id,
            in_service
        FROM distribution_capacitors
        ORDER BY id
        """
    ).fetchall()
    if not capacitor_rows:
        return

    phase_equipment_cache: dict[int, PhaseCapacitorEquipment] = {}
    equipment_cache: dict[int, CapacitorEquipment] = {}

    for (
        capacitor_id,
        capacitor_name,
        bus_id,
        substation_id,
        feeder_id,
        capacitor_equipment_id,
        in_service,
    ) in capacitor_rows:
        phase_rows = conn.execute(
            "SELECT phase FROM distribution_capacitor_phases WHERE capacitor_id = ? ORDER BY position_index",
            (capacitor_id,),
        ).fetchall()
        phases = [Phase(phase) for (phase,) in phase_rows]

        equipment = _load_or_cache_capacitor_equipment(
            conn, capacitor_equipment_id, equipment_cache, phase_equipment_cache
        )

        controller_rows = conn.execute(
            """
            SELECT
                id,
                name,
                controller_type,
                delay_on,
                delay_on_unit,
                delay_off,
                delay_off_unit,
                dead_time,
                dead_time_unit,
                on_voltage,
                on_voltage_unit,
                off_voltage,
                off_voltage_unit,
                pt_ratio,
                on_active_power,
                on_active_power_unit,
                off_active_power,
                off_active_power_unit,
                on_reactive_power,
                on_reactive_power_unit,
                off_reactive_power,
                off_reactive_power_unit,
                on_current,
                on_current_unit,
                off_current,
                off_current_unit,
                ct_ratio,
                on_time,
                off_time
            FROM capacitor_controllers
            WHERE capacitor_id = ?
            ORDER BY position_index
            """,
            (capacitor_id,),
        ).fetchall()
        controllers = []
        for row in controller_rows:
            controller = _build_capacitor_controller(conn, row)
            if controller is not None:
                controllers.append(controller)

        capacitor = DistributionCapacitor(
            name=capacitor_name,
            bus=buses_by_id[bus_id],
            substation=substations_by_id[substation_id],
            feeder=feeders_by_id[feeder_id],
            phases=phases,
            controllers=controllers,
            equipment=equipment,
            in_service=bool(in_service),
        )
        capacitor_uuid = _fetch_component_uuid(conn, "distribution_capacitors", capacitor_id)
        if capacitor_uuid is not None:
            capacitor = capacitor.model_copy(update={"uuid": capacitor_uuid})
        system.add_component(capacitor)


def _load_distribution_voltage_sources_from_normalized(
    conn: sqlite3.Connection,
    system: DistributionSystem,
    buses_by_id: dict[int, DistributionBus],
    substations_by_id: dict[int, DistributionSubstation],
    feeders_by_id: dict[int, DistributionFeeder],
) -> None:
    vsource_rows = conn.execute(
        """
        SELECT
            id,
            name,
            bus_id,
            substation_id,
            feeder_id,
            voltage_source_equipment_id,
            in_service
        FROM distribution_voltage_sources
        ORDER BY id
        """
    ).fetchall()
    if not vsource_rows:
        return

    phase_source_cache: dict[int, PhaseVoltageSourceEquipment] = {}
    source_equipment_cache: dict[int, VoltageSourceEquipment] = {}

    for (
        vsource_id,
        name,
        bus_id,
        substation_id,
        feeder_id,
        source_equipment_id,
        in_service,
    ) in vsource_rows:
        source_equipment = source_equipment_cache.get(source_equipment_id)
        if source_equipment is None:
            equipment_row = conn.execute(
                "SELECT name FROM voltage_source_equipment WHERE id = ?",
                (source_equipment_id,),
            ).fetchone()
            if equipment_row is None:
                raise ValueError(f"voltage_source_equipment_id={source_equipment_id} not found")
            (equipment_name,) = equipment_row

            phase_links = conn.execute(
                """
                SELECT phase_source_equipment_id
                FROM voltage_source_phases
                WHERE voltage_source_equipment_id = ?
                ORDER BY position_index
                """,
                (source_equipment_id,),
            ).fetchall()
            sources: list[PhaseVoltageSourceEquipment] = []
            for (phase_source_id,) in phase_links:
                phase_source = phase_source_cache.get(phase_source_id)
                if phase_source is None:
                    source_row = conn.execute(
                        """
                        SELECT
                            name,
                            r0,
                            r0_unit,
                            r1,
                            r1_unit,
                            x0,
                            x0_unit,
                            x1,
                            x1_unit,
                            voltage,
                            voltage_unit,
                            voltage_type,
                            angle,
                            angle_unit
                        FROM phase_voltage_source_equipment
                        WHERE id = ?
                        """,
                        (phase_source_id,),
                    ).fetchone()
                    if source_row is None:
                        raise ValueError(
                            f"phase_voltage_source_equipment_id={phase_source_id} not found"
                        )
                    (
                        phase_name,
                        r0,
                        r0_unit,
                        r1,
                        r1_unit,
                        x0,
                        x0_unit,
                        x1,
                        x1_unit,
                        voltage,
                        voltage_unit,
                        voltage_type,
                        angle,
                        angle_unit,
                    ) = source_row
                    phase_source = PhaseVoltageSourceEquipment(
                        name=phase_name,
                        r0=Resistance(r0, r0_unit),
                        r1=Resistance(r1, r1_unit),
                        x0=Reactance(x0, x0_unit),
                        x1=Reactance(x1, x1_unit),
                        voltage=Voltage(voltage, voltage_unit),
                        voltage_type=VoltageTypes(voltage_type),
                        angle=Angle(angle, angle_unit),
                    )
                    phase_source_uuid = _fetch_component_uuid(
                        conn,
                        "phase_voltage_source_equipment",
                        phase_source_id,
                    )
                    if phase_source_uuid is not None:
                        phase_source = phase_source.model_copy(update={"uuid": phase_source_uuid})
                    phase_source_cache[phase_source_id] = phase_source
                sources.append(phase_source)

            source_equipment = VoltageSourceEquipment(name=equipment_name, sources=sources)
            source_equipment_uuid = _fetch_component_uuid(
                conn,
                "voltage_source_equipment",
                source_equipment_id,
            )
            if source_equipment_uuid is not None:
                source_equipment = source_equipment.model_copy(
                    update={"uuid": source_equipment_uuid}
                )
            source_equipment_cache[source_equipment_id] = source_equipment

        phase_rows = conn.execute(
            "SELECT phase FROM distribution_voltage_source_phases WHERE vsource_id = ? ORDER BY position_index",
            (vsource_id,),
        ).fetchall()
        phases = [Phase(phase) for (phase,) in phase_rows]

        vsource = DistributionVoltageSource(
            name=name,
            bus=buses_by_id[bus_id],
            substation=substations_by_id[substation_id],
            feeder=feeders_by_id[feeder_id],
            phases=phases,
            equipment=source_equipment,
            in_service=bool(in_service),
        )
        vsource_uuid = _fetch_component_uuid(conn, "distribution_voltage_sources", vsource_id)
        if vsource_uuid is not None:
            vsource = vsource.model_copy(update={"uuid": vsource_uuid})
        system.add_component(vsource)


def _load_distribution_transformers_from_normalized(
    conn: sqlite3.Connection,
    system: DistributionSystem,
    buses_by_id: dict[int, DistributionBus],
    substations_by_id: dict[int, DistributionSubstation],
    feeders_by_id: dict[int, DistributionFeeder],
) -> None:
    transformer_rows = conn.execute(
        """
        SELECT
            id,
            name,
            substation_id,
            feeder_id,
            equipment_id,
            in_service
        FROM distribution_transformers
        ORDER BY id
        """
    ).fetchall()
    if not transformer_rows:
        return

    equipment_cache: dict[int, DistributionTransformerEquipment] = {}

    for (
        transformer_id,
        name,
        substation_id,
        feeder_id,
        equipment_id,
        in_service,
    ) in transformer_rows:
        equipment = equipment_cache.get(equipment_id)
        if equipment is None:
            equipment = _load_transformer_equipment(conn, equipment_id)
            equipment_cache[equipment_id] = equipment

        winding_bus_rows = conn.execute(
            """
            SELECT winding_index, bus_id
            FROM transformer_winding_buses
            WHERE transformer_id = ?
            ORDER BY winding_index
            """,
            (transformer_id,),
        ).fetchall()
        buses = [buses_by_id[bus_id] for _, bus_id in winding_bus_rows]

        winding_phase_rows = conn.execute(
            """
            SELECT winding_index, phase, phase_index
            FROM transformer_winding_phases
            WHERE transformer_id = ?
            ORDER BY winding_index, phase_index
            """,
            (transformer_id,),
        ).fetchall()
        winding_phases: list[list[Phase]] = [[] for _ in range(len(buses))]
        for winding_index, phase, _ in winding_phase_rows:
            winding_phases[winding_index].append(Phase(phase))

        transformer = DistributionTransformer(
            name=name,
            buses=buses,
            substation=substations_by_id[substation_id],
            feeder=feeders_by_id[feeder_id],
            winding_phases=winding_phases,
            equipment=equipment,
            in_service=bool(in_service),
        )
        transformer_uuid = _fetch_component_uuid(conn, "distribution_transformers", transformer_id)
        if transformer_uuid is not None:
            transformer = transformer.model_copy(update={"uuid": transformer_uuid})
        system.add_component(transformer)


def _load_distribution_regulators_from_normalized(
    conn: sqlite3.Connection,
    system: DistributionSystem,
    buses_by_id: dict[int, DistributionBus],
    substations_by_id: dict[int, DistributionSubstation],
    feeders_by_id: dict[int, DistributionFeeder],
) -> None:
    regulator_rows = conn.execute(
        """
        SELECT
            id,
            name,
            substation_id,
            feeder_id,
            equipment_id,
            in_service
        FROM distribution_regulators
        ORDER BY id
        """
    ).fetchall()
    if not regulator_rows:
        return

    equipment_cache: dict[int, DistributionTransformerEquipment] = {}

    for (
        regulator_id,
        name,
        substation_id,
        feeder_id,
        equipment_id,
        in_service,
    ) in regulator_rows:
        equipment = equipment_cache.get(equipment_id)
        if equipment is None:
            equipment = _load_transformer_equipment(conn, equipment_id)
            equipment_cache[equipment_id] = equipment

        winding_bus_rows = conn.execute(
            """
            SELECT winding_index, bus_id
            FROM regulator_winding_buses
            WHERE regulator_id = ?
            ORDER BY winding_index
            """,
            (regulator_id,),
        ).fetchall()
        buses = [buses_by_id[bus_id] for _, bus_id in winding_bus_rows]

        winding_phase_rows = conn.execute(
            """
            SELECT winding_index, phase, phase_index
            FROM regulator_winding_phases
            WHERE regulator_id = ?
            ORDER BY winding_index, phase_index
            """,
            (regulator_id,),
        ).fetchall()
        winding_phases: list[list[Phase]] = [[] for _ in range(len(buses))]
        for winding_index, phase, _ in winding_phase_rows:
            winding_phases[winding_index].append(Phase(phase))

        controller_rows = conn.execute(
            """
            SELECT
                id,
                name,
                delay,
                delay_unit,
                v_setpoint,
                v_setpoint_unit,
                min_v_limit,
                min_v_limit_unit,
                max_v_limit,
                max_v_limit_unit,
                pt_ratio,
                use_ldc,
                is_reversible,
                ldc_R,
                ldc_R_unit,
                ldc_X,
                ldc_X_unit,
                ct_primary,
                ct_primary_unit,
                max_step,
                bandwidth,
                bandwidth_unit,
                controlled_bus_id,
                controlled_phase
            FROM regulator_controllers
            WHERE regulator_id = ?
            ORDER BY position_index
            """,
            (regulator_id,),
        ).fetchall()
        controllers: list[RegulatorController] = []
        for (
            controller_id,
            controller_name,
            delay,
            delay_unit,
            v_setpoint,
            v_setpoint_unit,
            min_v_limit,
            min_v_limit_unit,
            max_v_limit,
            max_v_limit_unit,
            pt_ratio,
            use_ldc,
            is_reversible,
            ldc_R,
            ldc_R_unit,
            ldc_X,
            ldc_X_unit,
            ct_primary,
            ct_primary_unit,
            max_step,
            bandwidth,
            bandwidth_unit,
            controlled_bus_id,
            controlled_phase,
        ) in controller_rows:
            controller = RegulatorController(
                name=controller_name,
                delay=Time(delay, delay_unit)
                if delay is not None and delay_unit is not None
                else None,
                v_setpoint=Voltage(v_setpoint, v_setpoint_unit),
                min_v_limit=Voltage(min_v_limit, min_v_limit_unit),
                max_v_limit=Voltage(max_v_limit, max_v_limit_unit),
                pt_ratio=pt_ratio,
                use_ldc=bool(use_ldc),
                is_reversible=bool(is_reversible),
                ldc_R=Voltage(ldc_R, ldc_R_unit)
                if ldc_R is not None and ldc_R_unit is not None
                else None,
                ldc_X=Voltage(ldc_X, ldc_X_unit)
                if ldc_X is not None and ldc_X_unit is not None
                else None,
                ct_primary=Current(ct_primary, ct_primary_unit)
                if ct_primary is not None and ct_primary_unit is not None
                else None,
                max_step=max_step,
                bandwidth=Voltage(bandwidth, bandwidth_unit),
                controlled_bus=buses_by_id[controlled_bus_id],
                controlled_phase=Phase(controlled_phase),
            )
            controller_uuid = _fetch_component_uuid(conn, "regulator_controllers", controller_id)
            if controller_uuid is not None:
                controller = controller.model_copy(update={"uuid": controller_uuid})
            controllers.append(controller)

        regulator = DistributionRegulator(
            name=name,
            buses=buses,
            substation=substations_by_id[substation_id],
            feeder=feeders_by_id[feeder_id],
            winding_phases=winding_phases,
            equipment=equipment,
            controllers=controllers,
            in_service=bool(in_service),
        )
        regulator_uuid = _fetch_component_uuid(conn, "distribution_regulators", regulator_id)
        if regulator_uuid is not None:
            regulator = regulator.model_copy(update={"uuid": regulator_uuid})
        system.add_component(regulator)


def _load_transformer_equipment(
    conn: sqlite3.Connection,
    equipment_id: int,
) -> DistributionTransformerEquipment:
    equipment_row = conn.execute(
        """
        SELECT
            name,
            mounting,
            pct_no_load_loss,
            pct_full_load_loss,
            is_center_tapped
        FROM distribution_transformer_equipment
        WHERE id = ?
        """,
        (equipment_id,),
    ).fetchone()
    if equipment_row is None:
        raise ValueError(f"distribution_transformer_equipment_id={equipment_id} not found")
    (
        equipment_name,
        mounting,
        pct_no_load_loss,
        pct_full_load_loss,
        is_center_tapped,
    ) = equipment_row

    winding_rows = conn.execute(
        """
        SELECT
            id,
            name,
            winding_index,
            resistance,
            is_grounded,
            rated_voltage,
            rated_voltage_unit,
            voltage_type,
            rated_power,
            rated_power_unit,
            num_phases,
            connection_type,
            total_taps,
            min_tap_pu,
            max_tap_pu
        FROM winding_equipment
        WHERE transformer_equipment_id = ?
        ORDER BY winding_index
        """,
        (equipment_id,),
    ).fetchall()
    windings: list[WindingEquipment] = []
    for (
        winding_id,
        winding_name,
        _,
        resistance,
        is_grounded,
        rated_voltage,
        rated_voltage_unit,
        voltage_type,
        rated_power,
        rated_power_unit,
        num_phases,
        connection_type,
        total_taps,
        min_tap_pu,
        max_tap_pu,
    ) in winding_rows:
        tap_rows = conn.execute(
            """
            SELECT tap_value
            FROM winding_tap_positions
            WHERE winding_id = ?
            ORDER BY position_index
            """,
            (winding_id,),
        ).fetchall()
        tap_positions = [tap for (tap,) in tap_rows]

        winding = WindingEquipment(
            name=winding_name,
            resistance=resistance,
            is_grounded=bool(is_grounded),
            rated_voltage=Voltage(rated_voltage, rated_voltage_unit),
            voltage_type=VoltageTypes(voltage_type),
            rated_power=ApparentPower(rated_power, rated_power_unit),
            num_phases=num_phases,
            connection_type=ConnectionType(connection_type),
            tap_positions=tap_positions,
            total_taps=total_taps,
            min_tap_pu=min_tap_pu,
            max_tap_pu=max_tap_pu,
        )
        winding_uuid = _fetch_component_uuid(conn, "winding_equipment", winding_id)
        if winding_uuid is not None:
            winding = winding.model_copy(update={"uuid": winding_uuid})
        windings.append(winding)

    coupling_rows = conn.execute(
        """
        SELECT from_winding_index, to_winding_index, reactance
        FROM transformer_coupling_sequences
        WHERE transformer_equipment_id = ?
        ORDER BY sequence_index
        """,
        (equipment_id,),
    ).fetchall()
    coupling_sequences = [SequencePair(a, b) for a, b, _ in coupling_rows]
    winding_reactances = [reactance for _, _, reactance in coupling_rows]

    equipment = DistributionTransformerEquipment(
        name=equipment_name,
        mounting=TransformerMounting(mounting),
        pct_no_load_loss=pct_no_load_loss,
        pct_full_load_loss=pct_full_load_loss,
        windings=windings,
        coupling_sequences=coupling_sequences,
        winding_reactances=winding_reactances,
        is_center_tapped=bool(is_center_tapped),
    )
    equipment_uuid = _fetch_component_uuid(
        conn,
        "distribution_transformer_equipment",
        equipment_id,
    )
    if equipment_uuid is not None:
        equipment = equipment.model_copy(update={"uuid": equipment_uuid})
    return equipment
