"""Load, solar, and battery read-write helpers for SQLite GDM persistence."""

from __future__ import annotations

import sqlite3
from uuid import UUID

from gdm.db.sqlite_store_controls_curves import (
    _load_inverter_controller,
    _upsert_inverter_controller,
)
from gdm.db.sqlite_store_identity import _fetch_component_uuid, _upsert_component_uuid_map
from gdm.distribution import DistributionSystem
from gdm.distribution.common.curve import Curve
from gdm.distribution.components import (
    DistributionBattery,
    DistributionBus,
    DistributionLoad,
    DistributionSolar,
)
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.controllers.distribution_inverter_controller import InverterController
from gdm.distribution.equipment.battery_equipment import BatteryEquipment
from gdm.distribution.equipment.inverter_equipment import InverterEquipment
from gdm.distribution.equipment.load_equipment import LoadEquipment
from gdm.distribution.equipment.phase_load_equipment import PhaseLoadEquipment
from gdm.distribution.equipment.solar_equipment import SolarEquipment
from gdm.distribution.enums import ConnectionType, Phase, VoltageTypes
from gdm.quantities import (
    ActivePower,
    ActivePowerOverTime,
    ApparentPower,
    EnergyDC,
    Irradiance,
    ReactivePower,
    Voltage,
)


def _write_distribution_loads(conn: sqlite3.Connection, system: DistributionSystem) -> None:
    bus_rows = conn.execute(
        "SELECT id, name, substation_id, feeder_id FROM distribution_buses"
    ).fetchall()
    bus_ref_by_name: dict[str, tuple[int, int, int]] = {
        name: (bus_id, substation_id, feeder_id)
        for bus_id, name, substation_id, feeder_id in bus_rows
    }

    phase_equipment_id_by_name: dict[str, int] = {}
    load_equipment_id_by_name: dict[str, int] = {}

    for load in system.get_components(DistributionLoad):
        bus_ref = bus_ref_by_name.get(load.bus.name)
        if bus_ref is None:
            raise ValueError(
                f"DistributionLoad '{load.name}' references missing bus '{load.bus.name}'"
            )

        bus_id, substation_id, feeder_id = bus_ref
        load_equipment_id = _upsert_load_equipment_chain(
            conn,
            load.equipment,
            phase_equipment_id_by_name,
            load_equipment_id_by_name,
        )

        cursor = conn.execute(
            """
            INSERT INTO distribution_loads(
                name, bus_id, substation_id, feeder_id, load_equipment_id, in_service
            )
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                load.name,
                bus_id,
                substation_id,
                feeder_id,
                load_equipment_id,
                1 if load.in_service else 0,
            ),
        )
        load_id = int(cursor.lastrowid)
        _upsert_component_uuid_map(conn, "distribution_loads", load_id, load.uuid)

        for position_index, phase in enumerate(load.phases):
            conn.execute(
                "INSERT INTO distribution_load_phases(load_id, phase, position_index) VALUES(?, ?, ?)",
                (load_id, phase.value, position_index),
            )


def _upsert_load_equipment_chain(
    conn: sqlite3.Connection,
    equipment: LoadEquipment,
    phase_equipment_id_by_name: dict[str, int],
    load_equipment_id_by_name: dict[str, int],
) -> int:
    load_equipment_id = load_equipment_id_by_name.get(equipment.name)
    if load_equipment_id is None:
        existing = conn.execute(
            "SELECT id FROM load_equipment WHERE name = ?",
            (equipment.name,),
        ).fetchone()
        if existing is None:
            cursor = conn.execute(
                "INSERT INTO load_equipment(name, connection_type) VALUES(?, ?)",
                (equipment.name, equipment.connection_type.value),
            )
            load_equipment_id = int(cursor.lastrowid)
        else:
            load_equipment_id = int(existing[0])
        load_equipment_id_by_name[equipment.name] = load_equipment_id
        _upsert_component_uuid_map(conn, "load_equipment", load_equipment_id, equipment.uuid)

        for position_index, phase_equipment in enumerate(equipment.phase_loads):
            phase_equipment_id = _upsert_phase_load_equipment(
                conn,
                phase_equipment,
                phase_equipment_id_by_name,
            )
            conn.execute(
                """
                INSERT INTO load_equipment_phases(
                    load_equipment_id,
                    phase_load_equipment_id,
                    position_index
                ) VALUES(?, ?, ?)
                """,
                (load_equipment_id, phase_equipment_id, position_index),
            )

    return load_equipment_id


def _upsert_phase_load_equipment(
    conn: sqlite3.Connection,
    phase_equipment: PhaseLoadEquipment,
    phase_equipment_id_by_name: dict[str, int],
) -> int:
    phase_equipment_id = phase_equipment_id_by_name.get(phase_equipment.name)
    if phase_equipment_id is None:
        existing = conn.execute(
            "SELECT id FROM phase_load_equipment WHERE name = ?",
            (phase_equipment.name,),
        ).fetchone()
        if existing is None:
            cursor = conn.execute(
                """
                INSERT INTO phase_load_equipment(
                    name,
                    real_power,
                    real_power_unit,
                    reactive_power,
                    reactive_power_unit,
                    z_real,
                    z_imag,
                    i_real,
                    i_imag,
                    p_real,
                    p_imag,
                    num_customers
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    phase_equipment.name,
                    float(phase_equipment.real_power.magnitude),
                    str(phase_equipment.real_power.units),
                    float(phase_equipment.reactive_power.magnitude),
                    str(phase_equipment.reactive_power.units),
                    phase_equipment.z_real,
                    phase_equipment.z_imag,
                    phase_equipment.i_real,
                    phase_equipment.i_imag,
                    phase_equipment.p_real,
                    phase_equipment.p_imag,
                    phase_equipment.num_customers,
                ),
            )
            phase_equipment_id = int(cursor.lastrowid)
        else:
            phase_equipment_id = int(existing[0])
        phase_equipment_id_by_name[phase_equipment.name] = phase_equipment_id
        _upsert_component_uuid_map(
            conn,
            "phase_load_equipment",
            phase_equipment_id,
            phase_equipment.uuid,
        )

    return phase_equipment_id


def _write_distribution_solar(
    conn: sqlite3.Connection,
    system: DistributionSystem,
    curve_id_by_uuid: dict[UUID, int],
    active_control_id_by_uuid: dict[UUID, int],
    reactive_control_id_by_uuid: dict[UUID, int],
    controller_id_by_uuid: dict[UUID, int],
) -> None:
    bus_rows = conn.execute(
        "SELECT id, name, substation_id, feeder_id FROM distribution_buses"
    ).fetchall()
    bus_ref_by_name: dict[str, tuple[int, int, int]] = {
        name: (bus_id, substation_id, feeder_id)
        for bus_id, name, substation_id, feeder_id in bus_rows
    }

    solar_equipment_id_by_name: dict[str, int] = {}
    inverter_equipment_id_by_name: dict[str, int] = {}
    for solar in system.get_components(DistributionSolar):
        bus_ref = bus_ref_by_name.get(solar.bus.name)
        if bus_ref is None:
            raise ValueError(
                f"DistributionSolar '{solar.name}' references missing bus '{solar.bus.name}'"
            )

        bus_id, substation_id, feeder_id = bus_ref

        solar_equipment_id = _upsert_solar_equipment(
            conn,
            solar.equipment,
            solar_equipment_id_by_name,
        )
        inverter_equipment_id = _upsert_inverter_equipment(
            conn,
            solar.inverter,
            inverter_equipment_id_by_name,
        )
        inverter_controller_id = _upsert_inverter_controller(
            conn,
            solar.controller,
            curve_id_by_uuid,
            active_control_id_by_uuid,
            reactive_control_id_by_uuid,
            controller_id_by_uuid,
        )

        cursor = conn.execute(
            """
            INSERT INTO distribution_solar(
                name,
                bus_id,
                substation_id,
                feeder_id,
                irradiance,
                irradiance_unit,
                active_power,
                active_power_unit,
                reactive_power,
                reactive_power_unit,
                solar_equipment_id,
                inverter_equipment_id,
                inverter_controller_id,
                in_service
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                solar.name,
                bus_id,
                substation_id,
                feeder_id,
                float(solar.irradiance.magnitude),
                str(solar.irradiance.units),
                float(solar.active_power.magnitude),
                str(solar.active_power.units),
                float(solar.reactive_power.magnitude),
                str(solar.reactive_power.units),
                solar_equipment_id,
                inverter_equipment_id,
                inverter_controller_id,
                1 if solar.in_service else 0,
            ),
        )
        solar_id = int(cursor.lastrowid)
        _upsert_component_uuid_map(conn, "distribution_solar", solar_id, solar.uuid)

        for position_index, phase in enumerate(solar.phases):
            conn.execute(
                "INSERT INTO distribution_solar_phases(solar_id, phase, position_index) VALUES(?, ?, ?)",
                (solar_id, phase.value, position_index),
            )


def _upsert_solar_equipment(
    conn: sqlite3.Connection,
    equipment: SolarEquipment,
    solar_equipment_id_by_name: dict[str, int],
) -> int:
    solar_equipment_id = solar_equipment_id_by_name.get(equipment.name)
    if solar_equipment_id is None:
        existing = conn.execute(
            "SELECT id FROM solar_equipment WHERE name = ?",
            (equipment.name,),
        ).fetchone()
        if existing is None:
            cursor = conn.execute(
                """
                INSERT INTO solar_equipment(
                    name,
                    rated_power,
                    rated_power_unit,
                    power_temp_curve_id,
                    resistance,
                    reactance,
                    rated_voltage,
                    rated_voltage_unit,
                    voltage_type
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    equipment.name,
                    float(equipment.rated_power.magnitude),
                    str(equipment.rated_power.units),
                    None,
                    equipment.resistance,
                    equipment.reactance,
                    float(equipment.rated_voltage.magnitude),
                    str(equipment.rated_voltage.units),
                    equipment.voltage_type.value,
                ),
            )
            solar_equipment_id = int(cursor.lastrowid)
        else:
            solar_equipment_id = int(existing[0])
        solar_equipment_id_by_name[equipment.name] = solar_equipment_id
        _upsert_component_uuid_map(conn, "solar_equipment", solar_equipment_id, equipment.uuid)

    return solar_equipment_id


def _upsert_inverter_equipment(
    conn: sqlite3.Connection,
    equipment: InverterEquipment,
    inverter_equipment_id_by_name: dict[str, int],
) -> int:
    inverter_equipment_id = inverter_equipment_id_by_name.get(equipment.name)
    if inverter_equipment_id is None:
        existing = conn.execute(
            "SELECT id FROM inverter_equipment WHERE name = ?",
            (equipment.name,),
        ).fetchone()
        if existing is None:
            cursor = conn.execute(
                """
                INSERT INTO inverter_equipment(
                    name,
                    rated_apparent_power,
                    rated_apparent_power_unit,
                    rise_limit,
                    rise_limit_unit,
                    fall_limit,
                    fall_limit_unit,
                    cutout_percent,
                    cutin_percent,
                    dc_to_ac_efficiency,
                    eff_curve_id
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    equipment.name,
                    float(equipment.rated_apparent_power.magnitude),
                    str(equipment.rated_apparent_power.units),
                    float(equipment.rise_limit.magnitude)
                    if equipment.rise_limit is not None
                    else None,
                    str(equipment.rise_limit.units) if equipment.rise_limit is not None else None,
                    float(equipment.fall_limit.magnitude)
                    if equipment.fall_limit is not None
                    else None,
                    str(equipment.fall_limit.units) if equipment.fall_limit is not None else None,
                    equipment.cutout_percent,
                    equipment.cutin_percent,
                    equipment.dc_to_ac_efficiency,
                    None,
                ),
            )
            inverter_equipment_id = int(cursor.lastrowid)
        else:
            inverter_equipment_id = int(existing[0])
        inverter_equipment_id_by_name[equipment.name] = inverter_equipment_id
        _upsert_component_uuid_map(
            conn,
            "inverter_equipment",
            inverter_equipment_id,
            equipment.uuid,
        )

    return inverter_equipment_id


def _write_distribution_batteries(
    conn: sqlite3.Connection,
    system: DistributionSystem,
    curve_id_by_uuid: dict[UUID, int],
    active_control_id_by_uuid: dict[UUID, int],
    reactive_control_id_by_uuid: dict[UUID, int],
    controller_id_by_uuid: dict[UUID, int],
) -> None:
    bus_rows = conn.execute(
        "SELECT id, name, substation_id, feeder_id FROM distribution_buses"
    ).fetchall()
    bus_ref_by_name: dict[str, tuple[int, int, int]] = {
        name: (bus_id, substation_id, feeder_id)
        for bus_id, name, substation_id, feeder_id in bus_rows
    }

    battery_equipment_id_by_name: dict[str, int] = {}
    inverter_equipment_id_by_name: dict[str, int] = {}

    for battery in system.get_components(DistributionBattery):
        bus_ref = bus_ref_by_name.get(battery.bus.name)
        if bus_ref is None:
            raise ValueError(
                f"DistributionBattery '{battery.name}' references missing bus '{battery.bus.name}'"
            )

        bus_id, substation_id, feeder_id = bus_ref

        battery_equipment_id = _upsert_battery_equipment(
            conn,
            battery.equipment,
            battery_equipment_id_by_name,
        )
        inverter_equipment_id = _upsert_inverter_equipment(
            conn,
            battery.inverter,
            inverter_equipment_id_by_name,
        )
        inverter_controller_id = _upsert_inverter_controller(
            conn,
            battery.controller,
            curve_id_by_uuid,
            active_control_id_by_uuid,
            reactive_control_id_by_uuid,
            controller_id_by_uuid,
        )

        cursor = conn.execute(
            """
            INSERT INTO distribution_batteries(
                name,
                bus_id,
                substation_id,
                feeder_id,
                active_power,
                active_power_unit,
                reactive_power,
                reactive_power_unit,
                battery_equipment_id,
                inverter_equipment_id,
                inverter_controller_id,
                in_service
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                battery.name,
                bus_id,
                substation_id,
                feeder_id,
                float(battery.active_power.magnitude),
                str(battery.active_power.units),
                float(battery.reactive_power.magnitude),
                str(battery.reactive_power.units),
                battery_equipment_id,
                inverter_equipment_id,
                inverter_controller_id,
                1 if battery.in_service else 0,
            ),
        )
        battery_id = int(cursor.lastrowid)
        _upsert_component_uuid_map(conn, "distribution_batteries", battery_id, battery.uuid)

        for position_index, phase in enumerate(battery.phases):
            conn.execute(
                "INSERT INTO distribution_battery_phases(battery_id, phase, position_index) VALUES(?, ?, ?)",
                (battery_id, phase.value, position_index),
            )


def _upsert_battery_equipment(
    conn: sqlite3.Connection,
    equipment: BatteryEquipment,
    battery_equipment_id_by_name: dict[str, int],
) -> int:
    battery_equipment_id = battery_equipment_id_by_name.get(equipment.name)
    if battery_equipment_id is None:
        existing = conn.execute(
            "SELECT id FROM battery_equipment WHERE name = ?",
            (equipment.name,),
        ).fetchone()
        if existing is None:
            cursor = conn.execute(
                """
                INSERT INTO battery_equipment(
                    name,
                    rated_energy,
                    rated_energy_unit,
                    rated_power,
                    rated_power_unit,
                    charging_efficiency,
                    discharging_efficiency,
                    idling_efficiency,
                    rated_voltage,
                    rated_voltage_unit,
                    voltage_type
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    equipment.name,
                    float(equipment.rated_energy.magnitude),
                    str(equipment.rated_energy.units),
                    float(equipment.rated_power.magnitude),
                    str(equipment.rated_power.units),
                    equipment.charging_efficiency,
                    equipment.discharging_efficiency,
                    equipment.idling_efficiency,
                    float(equipment.rated_voltage.magnitude),
                    str(equipment.rated_voltage.units),
                    equipment.voltage_type.value,
                ),
            )
            battery_equipment_id = int(cursor.lastrowid)
        else:
            battery_equipment_id = int(existing[0])
        battery_equipment_id_by_name[equipment.name] = battery_equipment_id
        _upsert_component_uuid_map(
            conn,
            "battery_equipment",
            battery_equipment_id,
            equipment.uuid,
        )

    return battery_equipment_id


def _load_distribution_loads_from_normalized(
    conn: sqlite3.Connection,
    system: DistributionSystem,
    buses_by_id: dict[int, DistributionBus],
    substations_by_id: dict[int, DistributionSubstation],
    feeders_by_id: dict[int, DistributionFeeder],
) -> None:
    load_rows = conn.execute(
        """
        SELECT id, name, bus_id, substation_id, feeder_id, load_equipment_id, in_service
        FROM distribution_loads
        ORDER BY id
        """
    ).fetchall()
    if not load_rows:
        return

    phase_equipment_cache: dict[int, PhaseLoadEquipment] = {}
    load_equipment_cache: dict[int, LoadEquipment] = {}

    for (
        load_id,
        load_name,
        bus_id,
        substation_id,
        feeder_id,
        load_equipment_id,
        in_service,
    ) in load_rows:
        load_phase_rows = conn.execute(
            "SELECT phase FROM distribution_load_phases WHERE load_id = ? ORDER BY position_index",
            (load_id,),
        ).fetchall()
        phases = [Phase(phase) for (phase,) in load_phase_rows]

        load_equipment = load_equipment_cache.get(load_equipment_id)
        if load_equipment is None:
            equipment_row = conn.execute(
                "SELECT name, connection_type FROM load_equipment WHERE id = ?",
                (load_equipment_id,),
            ).fetchone()
            if equipment_row is None:
                raise ValueError(f"load_equipment_id={load_equipment_id} not found")
            equipment_name, connection_type = equipment_row

            phase_link_rows = conn.execute(
                """
                SELECT phase_load_equipment_id
                FROM load_equipment_phases
                WHERE load_equipment_id = ?
                ORDER BY position_index
                """,
                (load_equipment_id,),
            ).fetchall()
            phase_loads: list[PhaseLoadEquipment] = []
            for (phase_equipment_id,) in phase_link_rows:
                phase_equipment = phase_equipment_cache.get(phase_equipment_id)
                if phase_equipment is None:
                    phase_row = conn.execute(
                        """
                        SELECT
                            name,
                            real_power,
                            real_power_unit,
                            reactive_power,
                            reactive_power_unit,
                            z_real,
                            z_imag,
                            i_real,
                            i_imag,
                            p_real,
                            p_imag,
                            num_customers
                        FROM phase_load_equipment
                        WHERE id = ?
                        """,
                        (phase_equipment_id,),
                    ).fetchone()
                    if phase_row is None:
                        raise ValueError(f"phase_load_equipment_id={phase_equipment_id} not found")

                    (
                        phase_name,
                        real_power,
                        real_power_unit,
                        reactive_power,
                        reactive_power_unit,
                        z_real,
                        z_imag,
                        i_real,
                        i_imag,
                        p_real,
                        p_imag,
                        num_customers,
                    ) = phase_row

                    phase_equipment = PhaseLoadEquipment(
                        name=phase_name,
                        real_power=ActivePower(real_power, real_power_unit),
                        reactive_power=ReactivePower(reactive_power, reactive_power_unit),
                        z_real=z_real,
                        z_imag=z_imag,
                        i_real=i_real,
                        i_imag=i_imag,
                        p_real=p_real,
                        p_imag=p_imag,
                        num_customers=num_customers,
                    )
                    phase_uuid = _fetch_component_uuid(
                        conn,
                        "phase_load_equipment",
                        phase_equipment_id,
                    )
                    if phase_uuid is not None:
                        phase_equipment = phase_equipment.model_copy(update={"uuid": phase_uuid})
                    phase_equipment_cache[phase_equipment_id] = phase_equipment
                phase_loads.append(phase_equipment)

            load_equipment = LoadEquipment(
                name=equipment_name,
                phase_loads=phase_loads,
                connection_type=ConnectionType(connection_type),
            )
            load_equipment_uuid = _fetch_component_uuid(conn, "load_equipment", load_equipment_id)
            if load_equipment_uuid is not None:
                load_equipment = load_equipment.model_copy(update={"uuid": load_equipment_uuid})
            load_equipment_cache[load_equipment_id] = load_equipment

        load = DistributionLoad(
            name=load_name,
            bus=buses_by_id[bus_id],
            substation=substations_by_id[substation_id],
            feeder=feeders_by_id[feeder_id],
            phases=phases,
            equipment=load_equipment,
            in_service=bool(in_service),
        )
        load_uuid = _fetch_component_uuid(conn, "distribution_loads", load_id)
        if load_uuid is not None:
            load = load.model_copy(update={"uuid": load_uuid})
        system.add_component(load)


def _load_distribution_solar_from_normalized(
    conn: sqlite3.Connection,
    system: DistributionSystem,
    buses_by_id: dict[int, DistributionBus],
    substations_by_id: dict[int, DistributionSubstation],
    feeders_by_id: dict[int, DistributionFeeder],
) -> None:
    solar_rows = conn.execute(
        """
        SELECT
            id,
            name,
            bus_id,
            substation_id,
            feeder_id,
            irradiance,
            irradiance_unit,
            active_power,
            active_power_unit,
            reactive_power,
            reactive_power_unit,
            solar_equipment_id,
            inverter_equipment_id,
            inverter_controller_id,
            in_service
        FROM distribution_solar
        ORDER BY id
        """
    ).fetchall()
    if not solar_rows:
        return

    solar_equipment_cache: dict[int, SolarEquipment] = {}
    inverter_equipment_cache: dict[int, InverterEquipment] = {}
    curve_cache: dict[int, Curve] = {}
    active_control_cache: dict[int, object] = {}
    reactive_control_cache: dict[int, object] = {}
    controller_cache: dict[int, InverterController] = {}

    for (
        solar_id,
        solar_name,
        bus_id,
        substation_id,
        feeder_id,
        irradiance,
        irradiance_unit,
        active_power,
        active_power_unit,
        reactive_power,
        reactive_power_unit,
        solar_equipment_id,
        inverter_equipment_id,
        inverter_controller_id,
        in_service,
    ) in solar_rows:
        phase_rows = conn.execute(
            "SELECT phase FROM distribution_solar_phases WHERE solar_id = ? ORDER BY position_index",
            (solar_id,),
        ).fetchall()
        phases = [Phase(phase) for (phase,) in phase_rows]

        solar_equipment = solar_equipment_cache.get(solar_equipment_id)
        if solar_equipment is None:
            equipment_row = conn.execute(
                """
                SELECT name, rated_power, rated_power_unit, resistance, reactance,
                       rated_voltage, rated_voltage_unit, voltage_type
                FROM solar_equipment
                WHERE id = ?
                """,
                (solar_equipment_id,),
            ).fetchone()
            if equipment_row is None:
                raise ValueError(f"solar_equipment_id={solar_equipment_id} not found")
            (
                equipment_name,
                rated_power,
                rated_power_unit,
                resistance,
                reactance,
                rated_voltage,
                rated_voltage_unit,
                voltage_type,
            ) = equipment_row
            solar_equipment = SolarEquipment(
                name=equipment_name,
                rated_power=ActivePower(rated_power, rated_power_unit),
                power_temp_curve=None,
                resistance=resistance,
                reactance=reactance,
                rated_voltage=Voltage(rated_voltage, rated_voltage_unit),
                voltage_type=VoltageTypes(voltage_type),
            )
            solar_equipment_uuid = _fetch_component_uuid(
                conn, "solar_equipment", solar_equipment_id
            )
            if solar_equipment_uuid is not None:
                solar_equipment = solar_equipment.model_copy(update={"uuid": solar_equipment_uuid})
            solar_equipment_cache[solar_equipment_id] = solar_equipment

        inverter_equipment = inverter_equipment_cache.get(inverter_equipment_id)
        if inverter_equipment is None:
            inverter_row = conn.execute(
                """
                SELECT name, rated_apparent_power, rated_apparent_power_unit,
                       rise_limit, rise_limit_unit, fall_limit, fall_limit_unit,
                       cutout_percent, cutin_percent, dc_to_ac_efficiency
                FROM inverter_equipment
                WHERE id = ?
                """,
                (inverter_equipment_id,),
            ).fetchone()
            if inverter_row is None:
                raise ValueError(f"inverter_equipment_id={inverter_equipment_id} not found")
            (
                inverter_name,
                rated_apparent_power,
                rated_apparent_power_unit,
                rise_limit,
                rise_limit_unit,
                fall_limit,
                fall_limit_unit,
                cutout_percent,
                cutin_percent,
                dc_to_ac_efficiency,
            ) = inverter_row
            inverter_equipment = InverterEquipment(
                name=inverter_name,
                rated_apparent_power=ApparentPower(
                    rated_apparent_power, rated_apparent_power_unit
                ),
                rise_limit=(
                    ActivePowerOverTime(rise_limit, rise_limit_unit)
                    if rise_limit is not None and rise_limit_unit is not None
                    else None
                ),
                fall_limit=(
                    ActivePowerOverTime(fall_limit, fall_limit_unit)
                    if fall_limit is not None and fall_limit_unit is not None
                    else None
                ),
                cutout_percent=cutout_percent,
                cutin_percent=cutin_percent,
                dc_to_ac_efficiency=dc_to_ac_efficiency,
                eff_curve=None,
            )
            inverter_equipment_uuid = _fetch_component_uuid(
                conn,
                "inverter_equipment",
                inverter_equipment_id,
            )
            if inverter_equipment_uuid is not None:
                inverter_equipment = inverter_equipment.model_copy(
                    update={"uuid": inverter_equipment_uuid}
                )
            inverter_equipment_cache[inverter_equipment_id] = inverter_equipment

        inverter_controller = None
        if inverter_controller_id is not None:
            inverter_controller = _load_inverter_controller(
                conn,
                inverter_controller_id,
                curve_cache,
                active_control_cache,
                reactive_control_cache,
                controller_cache,
            )

        solar = DistributionSolar(
            name=solar_name,
            bus=buses_by_id[bus_id],
            substation=substations_by_id[substation_id],
            feeder=feeders_by_id[feeder_id],
            phases=phases,
            irradiance=Irradiance(irradiance, irradiance_unit),
            active_power=ActivePower(active_power, active_power_unit),
            reactive_power=ReactivePower(reactive_power, reactive_power_unit),
            controller=inverter_controller,
            inverter=inverter_equipment,
            equipment=solar_equipment,
            in_service=bool(in_service),
        )
        solar_uuid = _fetch_component_uuid(conn, "distribution_solar", solar_id)
        if solar_uuid is not None:
            solar = solar.model_copy(update={"uuid": solar_uuid})
        system.add_component(solar)


def _load_distribution_batteries_from_normalized(
    conn: sqlite3.Connection,
    system: DistributionSystem,
    buses_by_id: dict[int, DistributionBus],
    substations_by_id: dict[int, DistributionSubstation],
    feeders_by_id: dict[int, DistributionFeeder],
) -> None:
    battery_rows = conn.execute(
        """
        SELECT
            id,
            name,
            bus_id,
            substation_id,
            feeder_id,
            active_power,
            active_power_unit,
            reactive_power,
            reactive_power_unit,
            battery_equipment_id,
            inverter_equipment_id,
            inverter_controller_id,
            in_service
        FROM distribution_batteries
        ORDER BY id
        """
    ).fetchall()
    if not battery_rows:
        return

    battery_equipment_cache: dict[int, BatteryEquipment] = {}
    inverter_equipment_cache: dict[int, InverterEquipment] = {}
    curve_cache: dict[int, Curve] = {}
    active_control_cache: dict[int, object] = {}
    reactive_control_cache: dict[int, object] = {}
    controller_cache: dict[int, InverterController] = {}

    for (
        battery_id,
        battery_name,
        bus_id,
        substation_id,
        feeder_id,
        active_power,
        active_power_unit,
        reactive_power,
        reactive_power_unit,
        battery_equipment_id,
        inverter_equipment_id,
        inverter_controller_id,
        in_service,
    ) in battery_rows:
        phase_rows = conn.execute(
            "SELECT phase FROM distribution_battery_phases WHERE battery_id = ? ORDER BY position_index",
            (battery_id,),
        ).fetchall()
        phases = [Phase(phase) for (phase,) in phase_rows]

        battery_equipment = battery_equipment_cache.get(battery_equipment_id)
        if battery_equipment is None:
            equipment_row = conn.execute(
                """
                SELECT
                    name,
                    rated_energy,
                    rated_energy_unit,
                    rated_power,
                    rated_power_unit,
                    charging_efficiency,
                    discharging_efficiency,
                    idling_efficiency,
                    rated_voltage,
                    rated_voltage_unit,
                    voltage_type
                FROM battery_equipment
                WHERE id = ?
                """,
                (battery_equipment_id,),
            ).fetchone()
            if equipment_row is None:
                raise ValueError(f"battery_equipment_id={battery_equipment_id} not found")

            (
                equipment_name,
                rated_energy,
                rated_energy_unit,
                rated_power,
                rated_power_unit,
                charging_efficiency,
                discharging_efficiency,
                idling_efficiency,
                rated_voltage,
                rated_voltage_unit,
                voltage_type,
            ) = equipment_row

            battery_equipment = BatteryEquipment(
                name=equipment_name,
                rated_energy=EnergyDC(rated_energy, rated_energy_unit),
                rated_power=ActivePower(rated_power, rated_power_unit),
                charging_efficiency=charging_efficiency,
                discharging_efficiency=discharging_efficiency,
                idling_efficiency=idling_efficiency,
                rated_voltage=Voltage(rated_voltage, rated_voltage_unit),
                voltage_type=VoltageTypes(voltage_type),
            )
            battery_equipment_uuid = _fetch_component_uuid(
                conn,
                "battery_equipment",
                battery_equipment_id,
            )
            if battery_equipment_uuid is not None:
                battery_equipment = battery_equipment.model_copy(
                    update={"uuid": battery_equipment_uuid}
                )
            battery_equipment_cache[battery_equipment_id] = battery_equipment

        inverter_equipment = inverter_equipment_cache.get(inverter_equipment_id)
        if inverter_equipment is None:
            inverter_row = conn.execute(
                """
                SELECT name, rated_apparent_power, rated_apparent_power_unit,
                       rise_limit, rise_limit_unit, fall_limit, fall_limit_unit,
                       cutout_percent, cutin_percent, dc_to_ac_efficiency
                FROM inverter_equipment
                WHERE id = ?
                """,
                (inverter_equipment_id,),
            ).fetchone()
            if inverter_row is None:
                raise ValueError(f"inverter_equipment_id={inverter_equipment_id} not found")
            (
                inverter_name,
                rated_apparent_power,
                rated_apparent_power_unit,
                rise_limit,
                rise_limit_unit,
                fall_limit,
                fall_limit_unit,
                cutout_percent,
                cutin_percent,
                dc_to_ac_efficiency,
            ) = inverter_row
            inverter_equipment = InverterEquipment(
                name=inverter_name,
                rated_apparent_power=ApparentPower(
                    rated_apparent_power, rated_apparent_power_unit
                ),
                rise_limit=(
                    ActivePowerOverTime(rise_limit, rise_limit_unit)
                    if rise_limit is not None and rise_limit_unit is not None
                    else None
                ),
                fall_limit=(
                    ActivePowerOverTime(fall_limit, fall_limit_unit)
                    if fall_limit is not None and fall_limit_unit is not None
                    else None
                ),
                cutout_percent=cutout_percent,
                cutin_percent=cutin_percent,
                dc_to_ac_efficiency=dc_to_ac_efficiency,
                eff_curve=None,
            )
            inverter_equipment_uuid = _fetch_component_uuid(
                conn,
                "inverter_equipment",
                inverter_equipment_id,
            )
            if inverter_equipment_uuid is not None:
                inverter_equipment = inverter_equipment.model_copy(
                    update={"uuid": inverter_equipment_uuid}
                )
            inverter_equipment_cache[inverter_equipment_id] = inverter_equipment

        inverter_controller = None
        if inverter_controller_id is not None:
            inverter_controller = _load_inverter_controller(
                conn,
                inverter_controller_id,
                curve_cache,
                active_control_cache,
                reactive_control_cache,
                controller_cache,
            )

        battery = DistributionBattery(
            name=battery_name,
            bus=buses_by_id[bus_id],
            substation=substations_by_id[substation_id],
            feeder=feeders_by_id[feeder_id],
            phases=phases,
            active_power=ActivePower(active_power, active_power_unit),
            reactive_power=ReactivePower(reactive_power, reactive_power_unit),
            controller=inverter_controller,
            inverter=inverter_equipment,
            equipment=battery_equipment,
            in_service=bool(in_service),
        )
        battery_uuid = _fetch_component_uuid(conn, "distribution_batteries", battery_id)
        if battery_uuid is not None:
            battery = battery.model_copy(update={"uuid": battery_uuid})
        system.add_component(battery)
