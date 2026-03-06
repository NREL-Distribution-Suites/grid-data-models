"""SQLite persistence helpers for GDM systems.

This module provides an initial, transactional DB persistence layer that:
1) bootstraps the reference distribution schema,
2) stores system payloads in additive GDM-owned tables, and
3) reconstructs systems through existing JSON serialization routines.
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Type
from uuid import UUID

from loguru import logger

from infrasys import Location
from infrasys.time_series_models import NonSequentialTimeSeries, SingleTimeSeries

from gdm.distribution import DistributionSystem
from gdm.distribution.common.limitset import VoltageLimitSet
from gdm.distribution.components import (
    DistributionBus,
)
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.enums import (
    LimitType,
    Phase,
    VoltageTypes,
)
from gdm.db.sqlite_store_identity import _fetch_component_uuid, _upsert_component_uuid_map
from gdm.db.connection import sqlite_path_from_target
from gdm.db.connection import get_backend_name
from gdm.db.sqlite_store_schema import (
    _ensure_gdm_tables,
    _initialize_schema,
    _upsert_metadata,
)
from gdm.db.sqlite_store_switchgear_loaders import (
    _load_matrix_impedance_fuses_from_normalized,
    _load_matrix_impedance_reclosers_from_normalized,
    _load_matrix_impedance_switches_from_normalized,
)
from gdm.db.sqlite_store_geometry import (
    _load_geometry_branches_from_normalized,
)
from gdm.db.sqlite_store_switchgear_writers import (
    _write_geometry_branches,
    _write_matrix_impedance_fuses,
    _write_matrix_impedance_reclosers,
    _write_matrix_impedance_switches,
)
from gdm.db.sqlite_store_network_branches import (
    _load_matrix_impedance_branches_from_normalized,
    _load_sequence_impedance_branches_from_normalized,
    _write_matrix_impedance_branches,
    _write_sequence_impedance_branches,
)
from gdm.db.sqlite_store_load_solar_battery import (
    _load_distribution_batteries_from_normalized,
    _load_distribution_loads_from_normalized,
    _load_distribution_solar_from_normalized,
    _write_distribution_batteries,
    _write_distribution_loads,
    _write_distribution_solar,
)
from gdm.db.sqlite_store_cap_voltage_xfmr_reg import (
    _load_distribution_capacitors_from_normalized,
    _load_distribution_regulators_from_normalized,
    _load_distribution_transformers_from_normalized,
    _load_distribution_voltage_sources_from_normalized,
    _write_distribution_capacitors,
    _write_distribution_regulators,
    _write_distribution_transformers,
    _write_distribution_voltage_sources,
)
from gdm.db.sqlite_store_snapshot import (
    _decode_snapshot_payload,
    _restore_time_series_sidecar,
    _serialize_system_to_json_text,
)
from gdm.quantities import (
    Voltage,
)


DEFAULT_DB_FORMAT_VERSION = "1"


def write_system_to_db(
    *,
    system,
    db_path: str | Path | None = None,
    db_url: str | None = None,
    schema_path: str | Path | None = None,
    replace: bool = True,
    initialize_schema: bool = True,
    system_kind: str,
) -> None:
    """Write a system to SQLite with transactional replace semantics.

    Parameters
    ----------
    system : System
        The GDM system instance to serialize and persist.
    db_path : str | Path | None
        Legacy SQLite database path.
    db_url : str | None
        Database URL/DSN.
    schema_path : str | Path | None
        Optional path to SQL schema script. If omitted, repository default is used.
    replace : bool
        If True, existing snapshot for this system kind is replaced.
    initialize_schema : bool
        If True, bootstrap schema if missing.
    system_kind : str
        Logical discriminator for stored system payloads.
    """

    backend = get_backend_name(db_path=db_path, db_url=db_url)
    if backend != "sqlite":
        raise NotImplementedError(
            "PostgreSQL persistence is in progress. Current write path supports SQLite targets only."
        )

    db_path = sqlite_path_from_target(db_path=db_path, db_url=db_url)
    payload = _serialize_system_to_json_text(system)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        if initialize_schema:
            _initialize_schema(conn, schema_path=schema_path)

        _ensure_gdm_tables(conn)

        with conn:
            if replace:
                conn.execute(
                    "DELETE FROM gdm_system_snapshots WHERE system_kind = ?",
                    (system_kind,),
                )
            conn.execute(
                """
                INSERT OR REPLACE INTO gdm_system_snapshots(system_kind, payload_json, created_at)
                VALUES(?, ?, CURRENT_TIMESTAMP)
                """,
                (system_kind, payload),
            )
            if system_kind == "distribution":
                _write_distribution_topology(conn, system=system, replace=replace)
                _write_time_series_associations(conn, system=system, replace=replace)
                _upsert_metadata(
                    conn,
                    f"{system_kind}_storage_mode",
                    "snapshot+normalized+timeseries-associations-v1",
                )
            _upsert_metadata(conn, "gdm_db_format_version", DEFAULT_DB_FORMAT_VERSION)
            _upsert_metadata(
                conn, f"{system_kind}_data_format_version", system.data_format_version
            )


def load_system_from_db(
    *,
    system_cls: Type,
    db_path: str | Path | None = None,
    db_url: str | None = None,
    system_kind: str,
    prefer_normalized: bool = False,
) -> object:
    """Load a system from SQLite snapshot tables.

    Parameters
    ----------
    system_cls : Type
        Target class used for deserialization (`DistributionSystem`, `CatalogSystem`).
    db_path : str | Path | None
        Legacy SQLite database path.
    db_url : str | None
        Database URL/DSN.
    system_kind : str
        Logical discriminator for stored system payloads.

    Returns
    -------
    object
        Deserialized system instance.
    """

    backend = get_backend_name(db_path=db_path, db_url=db_url)
    if backend != "sqlite":
        raise NotImplementedError(
            "PostgreSQL persistence is in progress. Current load path supports SQLite targets only."
        )

    db_path = sqlite_path_from_target(db_path=db_path, db_url=db_url)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        if system_kind == "distribution" and prefer_normalized:
            normalized = _load_distribution_topology_from_normalized(conn)
            if normalized is not None:
                _attach_time_series_from_snapshot(conn, normalized)
                return normalized

        row = conn.execute(
            "SELECT payload_json FROM gdm_system_snapshots WHERE system_kind = ?",
            (system_kind,),
        ).fetchone()

    if row is None:
        raise ValueError(f"No persisted '{system_kind}' system found in {db_path}")

    payload = row[0]
    if not payload:
        raise ValueError(f"Persisted payload for '{system_kind}' is empty in {db_path}")

    snapshot = _decode_snapshot_payload(payload)
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_json = Path(tmp_dir) / f"{system_kind}_snapshot.json"
        temp_json.write_text(snapshot["system_json"])
        _restore_time_series_sidecar(Path(tmp_dir), snapshot)
        return system_cls.from_json(temp_json)


def _delete_distribution_tables(conn: sqlite3.Connection, component_types: set[str]) -> None:
    """Remove all distribution topology rows in correct dependency order."""
    conn.execute("DELETE FROM geometry_branch_phases")
    conn.execute("DELETE FROM geometry_branches")
    conn.execute("DELETE FROM geometry_branch_conductors")
    conn.execute("DELETE FROM geometry_branch_equipment")
    conn.execute("DELETE FROM matrix_impedance_fuse_phases")
    conn.execute("DELETE FROM fuse_phase_states")
    conn.execute("DELETE FROM matrix_impedance_fuses")
    conn.execute("DELETE FROM impedance_matrix_entries WHERE equipment_type = 'FUSE'")
    conn.execute("DELETE FROM matrix_impedance_fuse_equipment")
    conn.execute("DELETE FROM matrix_impedance_recloser_phases")
    conn.execute("DELETE FROM recloser_phase_states")
    conn.execute("DELETE FROM matrix_impedance_reclosers")
    conn.execute("DELETE FROM impedance_matrix_entries WHERE equipment_type = 'RECLOSER'")
    conn.execute("DELETE FROM matrix_impedance_recloser_equipment")
    conn.execute("DELETE FROM recloser_reclose_intervals")
    conn.execute("DELETE FROM recloser_controllers")
    conn.execute("DELETE FROM recloser_controller_equipment")
    conn.execute("DELETE FROM time_current_curve_points")
    conn.execute("DELETE FROM time_current_curves")
    conn.execute("DELETE FROM switch_phase_states")
    conn.execute("DELETE FROM matrix_impedance_switch_phases")
    conn.execute("DELETE FROM matrix_impedance_switches")
    conn.execute("DELETE FROM impedance_matrix_entries WHERE equipment_type = 'SWITCH'")
    conn.execute("DELETE FROM matrix_impedance_switch_equipment")
    conn.execute("DELETE FROM switch_controllers")
    conn.execute("DELETE FROM sequence_impedance_branch_phases")
    conn.execute("DELETE FROM sequence_impedance_branches")
    conn.execute("DELETE FROM sequence_impedance_branch_equipment")
    conn.execute("DELETE FROM matrix_impedance_branch_phases")
    conn.execute("DELETE FROM matrix_impedance_branches")
    conn.execute("DELETE FROM impedance_matrix_entries WHERE equipment_type = 'LINE'")
    conn.execute("DELETE FROM matrix_impedance_branch_equipment")
    conn.execute("DELETE FROM regulator_controllers")
    conn.execute("DELETE FROM regulator_winding_phases")
    conn.execute("DELETE FROM regulator_winding_buses")
    conn.execute("DELETE FROM distribution_regulators")
    conn.execute("DELETE FROM transformer_winding_phases")
    conn.execute("DELETE FROM transformer_winding_buses")
    conn.execute("DELETE FROM distribution_transformers")
    conn.execute("DELETE FROM winding_tap_positions")
    conn.execute("DELETE FROM winding_equipment")
    conn.execute("DELETE FROM transformer_coupling_sequences")
    conn.execute("DELETE FROM distribution_transformer_equipment")
    conn.execute("DELETE FROM distribution_voltage_source_phases")
    conn.execute("DELETE FROM distribution_voltage_sources")
    conn.execute("DELETE FROM voltage_source_phases")
    conn.execute("DELETE FROM voltage_source_equipment")
    conn.execute("DELETE FROM phase_voltage_source_equipment")
    conn.execute("DELETE FROM distribution_capacitor_phases")
    conn.execute("DELETE FROM capacitor_controllers")
    conn.execute("DELETE FROM distribution_capacitors")
    conn.execute("DELETE FROM capacitor_equipment_phases")
    conn.execute("DELETE FROM capacitor_equipment")
    conn.execute("DELETE FROM phase_capacitor_equipment")
    conn.execute("DELETE FROM distribution_battery_phases")
    conn.execute("DELETE FROM distribution_batteries")
    conn.execute("DELETE FROM battery_equipment")
    conn.execute("DELETE FROM inverter_controllers")
    conn.execute("DELETE FROM inverter_active_power_controls")
    conn.execute("DELETE FROM inverter_reactive_power_controls")
    conn.execute("DELETE FROM curve_points")
    conn.execute("DELETE FROM curves")
    conn.execute("DELETE FROM distribution_solar_phases")
    conn.execute("DELETE FROM distribution_solar")
    conn.execute("DELETE FROM solar_equipment")
    conn.execute("DELETE FROM inverter_equipment")
    conn.execute("DELETE FROM distribution_load_phases")
    conn.execute("DELETE FROM distribution_loads")
    conn.execute("DELETE FROM load_equipment_phases")
    conn.execute("DELETE FROM load_equipment")
    conn.execute("DELETE FROM phase_load_equipment")
    conn.execute("DELETE FROM bus_voltage_limits")
    conn.execute("DELETE FROM bus_phases")
    conn.execute("DELETE FROM distribution_buses")
    conn.execute("DELETE FROM substation_feeders")
    conn.execute("DELETE FROM distribution_substations")
    conn.execute("DELETE FROM distribution_feeders")
    conn.execute(
        "DELETE FROM voltage_limit_sets WHERE id NOT IN (SELECT limit_set_id FROM bus_voltage_limits)"
    )
    conn.execute(
        f"DELETE FROM gdm_component_uuid_map WHERE component_type IN ({', '.join(['?'] * len(component_types))})",
        tuple(component_types),
    )


def _write_distribution_buses(
    conn: sqlite3.Connection,
    system: DistributionSystem,
    substation_id_by_name: dict[str, int],
    feeder_id_by_name: dict[str, int],
) -> None:
    """Persist all DistributionBus rows, phases, and voltage limits."""
    for bus in system.get_components(DistributionBus):
        if bus.substation is None or bus.feeder is None:
            raise ValueError(
                f"DistributionBus '{bus.name}' must have substation and feeder assigned for DB export"
            )

        substation_id = substation_id_by_name.get(bus.substation.name)
        feeder_id = feeder_id_by_name.get(bus.feeder.name)
        if substation_id is None or feeder_id is None:
            raise ValueError(
                f"DistributionBus '{bus.name}' references substation/feeder not present in system"
            )

        coordinate_x = bus.coordinate.x if bus.coordinate is not None else None
        coordinate_y = bus.coordinate.y if bus.coordinate is not None else None

        cursor = conn.execute(
            """
            INSERT INTO distribution_buses(
                name,
                substation_id,
                feeder_id,
                voltage_type,
                rated_voltage,
                rated_voltage_unit,
                coordinate_x,
                coordinate_y,
                in_service
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bus.name,
                substation_id,
                feeder_id,
                bus.voltage_type.value,
                float(bus.rated_voltage.magnitude),
                str(bus.rated_voltage.units),
                coordinate_x,
                coordinate_y,
                1 if bus.in_service else 0,
            ),
        )
        bus_id = int(cursor.lastrowid)
        _upsert_component_uuid_map(conn, "distribution_buses", bus_id, bus.uuid)

        for position_index, phase in enumerate(bus.phases):
            conn.execute(
                "INSERT INTO bus_phases(bus_id, phase, position_index) VALUES(?, ?, ?)",
                (bus_id, phase.value, position_index),
            )

        for limit_set in bus.voltagelimits:
            limit_cursor = conn.execute(
                "INSERT INTO voltage_limit_sets(name, limit_type, value, value_unit) VALUES(?, ?, ?, ?)",
                (
                    limit_set.name,
                    limit_set.limit_type.value,
                    float(limit_set.value.magnitude),
                    str(limit_set.value.units),
                ),
            )
            limit_id = int(limit_cursor.lastrowid)
            _upsert_component_uuid_map(conn, "voltage_limit_sets", limit_id, limit_set.uuid)
            conn.execute(
                "INSERT INTO bus_voltage_limits(bus_id, limit_set_id) VALUES(?, ?)",
                (bus_id, limit_id),
            )


def _write_distribution_topology(conn: sqlite3.Connection, system, replace: bool) -> None:
    if not isinstance(system, DistributionSystem):
        return

    component_types = {
        "distribution_feeders",
        "distribution_substations",
        "distribution_buses",
        "voltage_limit_sets",
        "distribution_loads",
        "distribution_load_phases",
        "load_equipment",
        "load_equipment_phases",
        "phase_load_equipment",
        "distribution_solar",
        "distribution_solar_phases",
        "solar_equipment",
        "inverter_equipment",
        "inverter_controllers",
        "inverter_active_power_controls",
        "inverter_reactive_power_controls",
        "curves",
        "distribution_batteries",
        "distribution_battery_phases",
        "battery_equipment",
        "distribution_capacitors",
        "distribution_capacitor_phases",
        "capacitor_controllers",
        "capacitor_equipment",
        "capacitor_equipment_phases",
        "phase_capacitor_equipment",
        "distribution_voltage_sources",
        "distribution_voltage_source_phases",
        "voltage_source_equipment",
        "voltage_source_phases",
        "phase_voltage_source_equipment",
        "distribution_transformers",
        "transformer_winding_buses",
        "transformer_winding_phases",
        "distribution_transformer_equipment",
        "winding_equipment",
        "winding_tap_positions",
        "transformer_coupling_sequences",
        "distribution_regulators",
        "regulator_winding_buses",
        "regulator_winding_phases",
        "regulator_controllers",
        "matrix_impedance_branches",
        "matrix_impedance_branch_phases",
        "matrix_impedance_branch_equipment",
        "sequence_impedance_branches",
        "sequence_impedance_branch_phases",
        "sequence_impedance_branch_equipment",
        "matrix_impedance_switches",
        "matrix_impedance_switch_phases",
        "switch_phase_states",
        "matrix_impedance_switch_equipment",
        "switch_controllers",
        "matrix_impedance_fuses",
        "matrix_impedance_fuse_phases",
        "fuse_phase_states",
        "matrix_impedance_fuse_equipment",
        "matrix_impedance_reclosers",
        "matrix_impedance_recloser_phases",
        "recloser_phase_states",
        "matrix_impedance_recloser_equipment",
        "recloser_controllers",
        "recloser_reclose_intervals",
        "recloser_controller_equipment",
        "time_current_curves",
        "geometry_branches",
        "geometry_branch_phases",
        "geometry_branch_equipment",
        "geometry_branch_conductors",
        "bare_conductor_equipment",
        "concentric_cable_equipment",
        "impedance_matrix_entries",
    }

    if replace:
        _delete_distribution_tables(conn, component_types)

    feeder_id_by_name: dict[str, int] = {}
    substation_id_by_name: dict[str, int] = {}

    feeders_by_name = {feeder.name: feeder for feeder in system.get_components(DistributionFeeder)}
    substations_by_name = {
        substation.name: substation for substation in system.get_components(DistributionSubstation)
    }
    for bus in system.get_components(DistributionBus):
        if bus.feeder is not None:
            feeders_by_name.setdefault(bus.feeder.name, bus.feeder)
        if bus.substation is not None:
            substations_by_name.setdefault(bus.substation.name, bus.substation)
    for substation in system.get_components(DistributionSubstation):
        for feeder in substation.feeders:
            feeders_by_name.setdefault(feeder.name, feeder)

    for feeder in feeders_by_name.values():
        cursor = conn.execute("INSERT INTO distribution_feeders(name) VALUES(?)", (feeder.name,))
        feeder_id = int(cursor.lastrowid)
        feeder_id_by_name[feeder.name] = feeder_id
        _upsert_component_uuid_map(conn, "distribution_feeders", feeder_id, feeder.uuid)

    for substation in substations_by_name.values():
        cursor = conn.execute(
            "INSERT INTO distribution_substations(name) VALUES(?)", (substation.name,)
        )
        substation_id = int(cursor.lastrowid)
        substation_id_by_name[substation.name] = substation_id
        _upsert_component_uuid_map(
            conn,
            "distribution_substations",
            substation_id,
            substation.uuid,
        )

        for feeder in substation.feeders:
            feeder_id = feeder_id_by_name.get(feeder.name)
            if feeder_id is None:
                raise ValueError(
                    f"Feeder '{feeder.name}' attached to substation '{substation.name}' was not found"
                )

            conn.execute(
                "INSERT INTO substation_feeders(substation_id, feeder_id) VALUES(?, ?)",
                (substation_id, feeder_id),
            )

    _write_distribution_buses(conn, system, substation_id_by_name, feeder_id_by_name)

    curve_id_by_uuid: dict[UUID, int] = {}
    active_control_id_by_uuid: dict[UUID, int] = {}
    reactive_control_id_by_uuid: dict[UUID, int] = {}
    controller_id_by_uuid: dict[UUID, int] = {}

    _write_distribution_loads(conn, system)
    _write_distribution_solar(
        conn,
        system,
        curve_id_by_uuid,
        active_control_id_by_uuid,
        reactive_control_id_by_uuid,
        controller_id_by_uuid,
    )
    _write_distribution_batteries(
        conn,
        system,
        curve_id_by_uuid,
        active_control_id_by_uuid,
        reactive_control_id_by_uuid,
        controller_id_by_uuid,
    )
    _write_distribution_capacitors(conn, system)
    _write_distribution_voltage_sources(conn, system)
    _write_distribution_transformers(conn, system)
    _write_distribution_regulators(conn, system)
    _write_matrix_impedance_branches(conn, system)
    _write_sequence_impedance_branches(conn, system)
    _write_matrix_impedance_switches(conn, system)
    _write_geometry_branches(conn, system)
    _write_matrix_impedance_fuses(conn, system)
    _write_matrix_impedance_reclosers(conn, system)


def _load_distribution_topology_from_normalized(
    conn: sqlite3.Connection,
) -> DistributionSystem | None:
    feeder_rows = conn.execute("SELECT id, name FROM distribution_feeders ORDER BY id").fetchall()
    substation_rows = conn.execute(
        "SELECT id, name FROM distribution_substations ORDER BY id"
    ).fetchall()
    bus_rows = conn.execute(
        """
        SELECT id, name, substation_id, feeder_id, voltage_type, rated_voltage,
               rated_voltage_unit, coordinate_x, coordinate_y, in_service
        FROM distribution_buses
        ORDER BY id
        """
    ).fetchall()

    if not feeder_rows and not substation_rows and not bus_rows:
        return None

    system = DistributionSystem(auto_add_composed_components=True)

    feeders_by_id: dict[int, DistributionFeeder] = {}
    for feeder_id, name in feeder_rows:
        feeder = DistributionFeeder(name=name)
        feeder_uuid = _fetch_component_uuid(conn, "distribution_feeders", feeder_id)
        if feeder_uuid is not None:
            feeder = feeder.model_copy(update={"uuid": feeder_uuid})
        system.add_component(feeder)
        feeders_by_id[feeder_id] = feeder

    substation_to_feeders = conn.execute(
        "SELECT substation_id, feeder_id FROM substation_feeders ORDER BY substation_id, feeder_id"
    ).fetchall()
    feeders_per_substation: dict[int, list[DistributionFeeder]] = {}
    for substation_id, feeder_id in substation_to_feeders:
        feeders_per_substation.setdefault(substation_id, []).append(feeders_by_id[feeder_id])

    substations_by_id: dict[int, DistributionSubstation] = {}
    for substation_id, name in substation_rows:
        feeders = feeders_per_substation.get(substation_id, [])
        substation = DistributionSubstation(name=name, feeders=feeders)
        substation_uuid = _fetch_component_uuid(conn, "distribution_substations", substation_id)
        if substation_uuid is not None:
            substation = substation.model_copy(update={"uuid": substation_uuid})
        system.add_component(substation)
        substations_by_id[substation_id] = substation

    buses_by_id: dict[int, DistributionBus] = {}

    for (
        bus_id,
        name,
        substation_id,
        feeder_id,
        voltage_type,
        rated_voltage,
        rated_voltage_unit,
        coordinate_x,
        coordinate_y,
        in_service,
    ) in bus_rows:
        phase_rows = conn.execute(
            "SELECT phase FROM bus_phases WHERE bus_id = ? ORDER BY position_index",
            (bus_id,),
        ).fetchall()
        phases = [Phase(phase) for (phase,) in phase_rows]

        limit_rows = conn.execute(
            """
            SELECT v.id, v.name, v.limit_type, v.value, v.value_unit
            FROM bus_voltage_limits bvl
            JOIN voltage_limit_sets v ON v.id = bvl.limit_set_id
            WHERE bvl.bus_id = ?
            ORDER BY v.id
            """,
            (bus_id,),
        ).fetchall()
        voltage_limits: list[VoltageLimitSet] = []
        for limit_id, limit_name, limit_type, limit_value, limit_unit in limit_rows:
            limit_set = VoltageLimitSet(
                name=limit_name,
                limit_type=LimitType(limit_type),
                value=Voltage(limit_value, limit_unit),
            )
            limit_uuid = _fetch_component_uuid(conn, "voltage_limit_sets", limit_id)
            if limit_uuid is not None:
                limit_set = limit_set.model_copy(update={"uuid": limit_uuid})
            voltage_limits.append(limit_set)

        coordinate = None
        if coordinate_x is not None and coordinate_y is not None:
            coordinate = Location(x=coordinate_x, y=coordinate_y)

        bus = DistributionBus(
            name=name,
            substation=substations_by_id[substation_id],
            feeder=feeders_by_id[feeder_id],
            voltage_type=VoltageTypes(voltage_type),
            phases=phases,
            voltagelimits=voltage_limits,
            rated_voltage=Voltage(rated_voltage, rated_voltage_unit),
            coordinate=coordinate,
            in_service=bool(in_service),
        )
        bus_uuid = _fetch_component_uuid(conn, "distribution_buses", bus_id)
        if bus_uuid is not None:
            bus = bus.model_copy(update={"uuid": bus_uuid})
        system.add_component(bus)
        buses_by_id[bus_id] = bus

    _load_distribution_loads_from_normalized(
        conn,
        system,
        buses_by_id=buses_by_id,
        substations_by_id=substations_by_id,
        feeders_by_id=feeders_by_id,
    )
    _load_distribution_solar_from_normalized(
        conn,
        system,
        buses_by_id=buses_by_id,
        substations_by_id=substations_by_id,
        feeders_by_id=feeders_by_id,
    )
    _load_distribution_batteries_from_normalized(
        conn,
        system,
        buses_by_id=buses_by_id,
        substations_by_id=substations_by_id,
        feeders_by_id=feeders_by_id,
    )
    _load_distribution_capacitors_from_normalized(
        conn,
        system,
        buses_by_id=buses_by_id,
        substations_by_id=substations_by_id,
        feeders_by_id=feeders_by_id,
    )
    _load_distribution_voltage_sources_from_normalized(
        conn,
        system,
        buses_by_id=buses_by_id,
        substations_by_id=substations_by_id,
        feeders_by_id=feeders_by_id,
    )
    _load_distribution_transformers_from_normalized(
        conn,
        system,
        buses_by_id=buses_by_id,
        substations_by_id=substations_by_id,
        feeders_by_id=feeders_by_id,
    )
    _load_distribution_regulators_from_normalized(
        conn,
        system,
        buses_by_id=buses_by_id,
        substations_by_id=substations_by_id,
        feeders_by_id=feeders_by_id,
    )
    _load_matrix_impedance_branches_from_normalized(
        conn,
        system,
        buses_by_id=buses_by_id,
        substations_by_id=substations_by_id,
        feeders_by_id=feeders_by_id,
    )
    _load_sequence_impedance_branches_from_normalized(
        conn,
        system,
        buses_by_id=buses_by_id,
        substations_by_id=substations_by_id,
        feeders_by_id=feeders_by_id,
    )
    _load_matrix_impedance_switches_from_normalized(
        conn,
        system,
        buses_by_id=buses_by_id,
        substations_by_id=substations_by_id,
        feeders_by_id=feeders_by_id,
    )
    _load_geometry_branches_from_normalized(
        conn,
        system,
        buses_by_id=buses_by_id,
        substations_by_id=substations_by_id,
        feeders_by_id=feeders_by_id,
    )
    _load_matrix_impedance_fuses_from_normalized(
        conn,
        system,
        buses_by_id=buses_by_id,
        substations_by_id=substations_by_id,
        feeders_by_id=feeders_by_id,
    )
    _load_matrix_impedance_reclosers_from_normalized(
        conn,
        system,
        buses_by_id=buses_by_id,
        substations_by_id=substations_by_id,
        feeders_by_id=feeders_by_id,
    )

    return system


def _component_type_for_time_series_owner(component) -> str | None:
    mapping = {
        "DistributionBus": "distribution_buses",
        "DistributionLoad": "distribution_loads",
        "DistributionSolar": "distribution_solar",
        "DistributionBattery": "distribution_batteries",
        "DistributionCapacitor": "distribution_capacitors",
        "DistributionVoltageSource": "distribution_voltage_sources",
        "DistributionTransformer": "distribution_transformers",
        "DistributionRegulator": "distribution_regulators",
        "MatrixImpedanceBranch": "matrix_impedance_branches",
        "SequenceImpedanceBranch": "sequence_impedance_branches",
        "GeometryBranch": "geometry_branches",
        "MatrixImpedanceFuse": "matrix_impedance_fuses",
        "MatrixImpedanceRecloser": "matrix_impedance_reclosers",
        "MatrixImpedanceSwitch": "matrix_impedance_switches",
    }
    return mapping.get(component.__class__.__name__)


def _write_time_series_associations(
    conn: sqlite3.Connection, system: DistributionSystem, replace: bool
) -> None:
    if replace:
        conn.execute("DELETE FROM time_series_associations")

    for component in system.iter_all_components():
        if not system.has_time_series(component):
            continue

        component_type = _component_type_for_time_series_owner(component)
        if component_type is None:
            continue

        owner_row = conn.execute(
            """
            SELECT component_id
            FROM gdm_component_uuid_map
            WHERE component_type = ? AND uuid = ?
            """,
            (component_type, str(component.uuid)),
        ).fetchone()
        if owner_row is None:
            continue
        owner_id = int(owner_row[0])
        owner_type = component.__class__.__name__

        for metadata in system.list_time_series_metadata(component):
            resolution = getattr(metadata, "resolution", None)
            initial_timestamp = getattr(metadata, "initial_timestamp", None)
            horizon = getattr(metadata, "horizon", None)
            interval = getattr(metadata, "interval", None)
            window_count = getattr(metadata, "window_count", None)
            length = getattr(metadata, "length", None)
            units = getattr(metadata, "units", None)
            normalization = getattr(metadata, "normalization", None)

            units_payload = (
                json.dumps(units.model_dump(), sort_keys=True)
                if units is not None and hasattr(units, "model_dump")
                else (str(units) if units is not None else None)
            )

            scaling_factor_multiplier = None
            if normalization is not None:
                scaling_factor_multiplier = str(
                    getattr(normalization, "scaling_factor_multiplier", normalization)
                )

            conn.execute(
                """
                INSERT OR REPLACE INTO time_series_associations(
                    time_series_uuid,
                    time_series_type,
                    initial_timestamp,
                    resolution,
                    horizon,
                    "interval",
                    window_count,
                    length,
                    name,
                    owner_id,
                    owner_type,
                    owner_category,
                    features,
                    scaling_factor_multiplier,
                    metadata_uuid,
                    units
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(metadata.time_series_uuid),
                    str(getattr(metadata, "type", metadata.__class__.__name__)),
                    initial_timestamp.isoformat() if initial_timestamp is not None else "",
                    str(resolution) if resolution is not None else "",
                    str(horizon) if horizon is not None else None,
                    str(interval) if interval is not None else None,
                    int(window_count) if window_count is not None else None,
                    int(length) if length is not None else None,
                    metadata.name,
                    owner_id,
                    owner_type,
                    "component",
                    json.dumps(metadata.features, sort_keys=True),
                    scaling_factor_multiplier,
                    str(metadata.uuid),
                    units_payload,
                ),
            )


def _attach_time_series_from_snapshot(
    conn: sqlite3.Connection, target_system: DistributionSystem
) -> None:
    row = conn.execute(
        "SELECT payload_json FROM gdm_system_snapshots WHERE system_kind = ?",
        ("distribution",),
    ).fetchone()
    if row is None:
        return

    snapshot = _decode_snapshot_payload(row[0])
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_json = Path(tmp_dir) / "distribution_snapshot.json"
        temp_json.write_text(snapshot["system_json"])
        _restore_time_series_sidecar(Path(tmp_dir), snapshot)
        source_system = DistributionSystem.from_json(temp_json)

    target_by_uuid = {
        component.uuid: component for component in target_system.iter_all_components()
    }

    for source_component in source_system.iter_all_components():
        target_component = target_by_uuid.get(source_component.uuid)
        if target_component is None:
            continue
        if not source_system.has_time_series(source_component):
            continue

        for metadata in source_system.list_time_series_metadata(source_component):
            try:
                ts_type_name = str(getattr(metadata, "type", ""))
                ts_data_type = {
                    "SingleTimeSeries": SingleTimeSeries,
                    "NonSequentialTimeSeries": NonSequentialTimeSeries,
                }.get(ts_type_name, SingleTimeSeries)
                ts_data = source_system.get_time_series(
                    source_component,
                    metadata.name,
                    ts_data_type,
                    **metadata.features,
                )
                target_system.add_time_series(ts_data, target_component, **metadata.features)
            except Exception:
                logger.debug(
                    "Failed to restore time series '{}' for component '{}'",
                    metadata.name,
                    source_component.name,
                )


def load_snapshot_payload(
    db_path: str | Path | None = None,
    system_kind: str = "distribution",
    db_url: str | None = None,
) -> dict:
    """Return raw snapshot payload as a JSON dictionary for inspection."""
    backend = get_backend_name(db_path=db_path, db_url=db_url)
    if backend != "sqlite":
        raise NotImplementedError(
            "PostgreSQL snapshot inspection is in progress. Current helper supports SQLite targets only."
        )

    db_path = sqlite_path_from_target(db_path=db_path, db_url=db_url)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT payload_json FROM gdm_system_snapshots WHERE system_kind = ?",
            (system_kind,),
        ).fetchone()
    if row is None:
        raise ValueError(f"No persisted '{system_kind}' system found in {db_path}")
    return json.loads(row[0])
