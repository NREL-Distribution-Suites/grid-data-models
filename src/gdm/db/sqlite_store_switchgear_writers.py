"""Switchgear and branch writer helpers for SQLite GDM persistence."""

from __future__ import annotations

import sqlite3
from uuid import UUID

from gdm.db.sqlite_store_controls_curves import _upsert_time_current_curve
from gdm.db.sqlite_store_geometry import _upsert_geometry_branch_equipment
from gdm.db.sqlite_store_identity import _upsert_component_uuid_map
from gdm.db.sqlite_store_impedance import _insert_impedance_matrix_entries
from gdm.db.sqlite_store_recloser import _upsert_distribution_recloser_controller
from gdm.distribution import DistributionSystem
from gdm.distribution.components import (
    GeometryBranch,
    MatrixImpedanceFuse,
    MatrixImpedanceRecloser,
    MatrixImpedanceSwitch,
)
from gdm.distribution.controllers.distribution_switch_controller import (
    DistributionSwitchController,
)
from gdm.distribution.equipment.matrix_impedance_fuse_equipment import MatrixImpedanceFuseEquipment
from gdm.distribution.equipment.matrix_impedance_recloser_equipment import (
    MatrixImpedanceRecloserEquipment,
)
from gdm.distribution.equipment.matrix_impedance_switch_equipment import (
    MatrixImpedanceSwitchEquipment,
)


def _resolve_branch_terminal_ids(
    conn: sqlite3.Connection,
    bus_ref_by_name: dict[str, tuple[int, int, int]],
    branch,
) -> tuple[int, int, int, int]:
    from_bus_ref = bus_ref_by_name.get(branch.buses[0].name)
    to_bus_ref = bus_ref_by_name.get(branch.buses[1].name)
    if from_bus_ref is None or to_bus_ref is None:
        raise ValueError(f"{type(branch).__name__} '{branch.name}' references unknown buses")

    from_bus_id, from_substation_id, from_feeder_id = from_bus_ref
    to_bus_id, _, _ = to_bus_ref

    substation_id = from_substation_id
    feeder_id = from_feeder_id
    if branch.substation is not None:
        row = conn.execute(
            "SELECT id FROM distribution_substations WHERE name = ?",
            (branch.substation.name,),
        ).fetchone()
        if row is not None:
            substation_id = int(row[0])
    if branch.feeder is not None:
        row = conn.execute(
            "SELECT id FROM distribution_feeders WHERE name = ?",
            (branch.feeder.name,),
        ).fetchone()
        if row is not None:
            feeder_id = int(row[0])

    return from_bus_id, to_bus_id, substation_id, feeder_id


def _write_matrix_impedance_switches(conn: sqlite3.Connection, system: DistributionSystem) -> None:
    bus_rows = conn.execute(
        "SELECT id, name, substation_id, feeder_id FROM distribution_buses"
    ).fetchall()
    bus_ref_by_name: dict[str, tuple[int, int, int]] = {
        name: (bus_id, substation_id, feeder_id)
        for bus_id, name, substation_id, feeder_id in bus_rows
    }
    equipment_id_by_name: dict[str, int] = {}
    switch_controller_id_by_uuid: dict[UUID, int] = {}

    for switch in system.get_components(MatrixImpedanceSwitch):
        from_bus_ref = bus_ref_by_name.get(switch.buses[0].name)
        to_bus_ref = bus_ref_by_name.get(switch.buses[1].name)
        if from_bus_ref is None or to_bus_ref is None:
            raise ValueError(f"MatrixImpedanceSwitch '{switch.name}' references unknown buses")

        from_bus_id, from_substation_id, from_feeder_id = from_bus_ref
        to_bus_id, _, _ = to_bus_ref

        substation_id = from_substation_id
        feeder_id = from_feeder_id
        if switch.substation is not None:
            row = conn.execute(
                "SELECT id FROM distribution_substations WHERE name = ?",
                (switch.substation.name,),
            ).fetchone()
            if row is not None:
                substation_id = int(row[0])
        if switch.feeder is not None:
            row = conn.execute(
                "SELECT id FROM distribution_feeders WHERE name = ?",
                (switch.feeder.name,),
            ).fetchone()
            if row is not None:
                feeder_id = int(row[0])

        equipment_id = _upsert_matrix_impedance_switch_equipment(
            conn,
            switch.equipment,
            equipment_id_by_name,
            switch_controller_id_by_uuid,
        )

        cursor = conn.execute(
            """
            INSERT INTO matrix_impedance_switches(
                name,
                from_bus_id,
                to_bus_id,
                substation_id,
                feeder_id,
                length,
                length_unit,
                equipment_id,
                in_service
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                switch.name,
                from_bus_id,
                to_bus_id,
                substation_id,
                feeder_id,
                float(switch.length.magnitude),
                str(switch.length.units),
                equipment_id,
                1 if switch.in_service else 0,
            ),
        )
        switch_id = int(cursor.lastrowid)
        _upsert_component_uuid_map(conn, "matrix_impedance_switches", switch_id, switch.uuid)

        for position_index, phase in enumerate(switch.phases):
            conn.execute(
                """
                INSERT INTO matrix_impedance_switch_phases(switch_id, phase, position_index)
                VALUES(?, ?, ?)
                """,
                (switch_id, phase.value, position_index),
            )
        for position_index, (phase, is_closed) in enumerate(zip(switch.phases, switch.is_closed)):
            conn.execute(
                """
                INSERT INTO switch_phase_states(
                    switch_id,
                    position_index,
                    phase,
                    is_closed
                ) VALUES(?, ?, ?, ?)
                """,
                (switch_id, position_index, phase.value, 1 if is_closed else 0),
            )


def _upsert_matrix_impedance_switch_equipment(
    conn: sqlite3.Connection,
    equipment: MatrixImpedanceSwitchEquipment,
    equipment_id_by_name: dict[str, int],
    switch_controller_id_by_uuid: dict[UUID, int],
) -> int:
    existing = equipment_id_by_name.get(equipment.name)
    if existing is not None:
        return existing

    row = conn.execute(
        "SELECT id FROM matrix_impedance_switch_equipment WHERE name = ?",
        (equipment.name,),
    ).fetchone()
    if row is not None:
        equipment_id = int(row[0])
        equipment_id_by_name[equipment.name] = equipment_id
        return equipment_id

    switch_controller_id: int | None = None
    if equipment.controller is not None:
        switch_controller_id = _upsert_switch_controller(
            conn,
            equipment.controller,
            switch_controller_id_by_uuid,
        )

    cursor = conn.execute(
        """
        INSERT INTO matrix_impedance_switch_equipment(
            name,
            construction,
            ampacity,
            ampacity_unit,
            switch_controller_id
        ) VALUES(?, ?, ?, ?, ?)
        """,
        (
            equipment.name,
            equipment.construction.value,
            float(equipment.ampacity.magnitude),
            str(equipment.ampacity.units),
            switch_controller_id,
        ),
    )
    equipment_id = int(cursor.lastrowid)
    _upsert_component_uuid_map(
        conn,
        "matrix_impedance_switch_equipment",
        equipment_id,
        equipment.uuid,
    )

    _insert_impedance_matrix_entries(
        conn,
        equipment_id,
        "SWITCH",
        "R",
        equipment.r_matrix.magnitude,
        str(equipment.r_matrix.units),
    )
    _insert_impedance_matrix_entries(
        conn,
        equipment_id,
        "SWITCH",
        "X",
        equipment.x_matrix.magnitude,
        str(equipment.x_matrix.units),
    )
    _insert_impedance_matrix_entries(
        conn,
        equipment_id,
        "SWITCH",
        "C",
        equipment.c_matrix.magnitude,
        str(equipment.c_matrix.units),
    )

    equipment_id_by_name[equipment.name] = equipment_id
    return equipment_id


def _upsert_switch_controller(
    conn: sqlite3.Connection,
    controller: DistributionSwitchController,
    switch_controller_id_by_uuid: dict[UUID, int],
) -> int:
    existing = switch_controller_id_by_uuid.get(controller.uuid)
    if existing is not None:
        return existing

    row = conn.execute(
        """
        SELECT id
        FROM switch_controllers
        WHERE name = ? AND delay = ? AND delay_unit = ? AND normal_state = ? AND is_locked = ?
        """,
        (
            controller.name,
            float(controller.delay.magnitude),
            str(controller.delay.units),
            controller.normal_state,
            1 if controller.is_locked else 0,
        ),
    ).fetchone()
    if row is None:
        cursor = conn.execute(
            """
            INSERT INTO switch_controllers(name, delay, delay_unit, normal_state, is_locked)
            VALUES(?, ?, ?, ?, ?)
            """,
            (
                controller.name,
                float(controller.delay.magnitude),
                str(controller.delay.units),
                controller.normal_state,
                1 if controller.is_locked else 0,
            ),
        )
        switch_controller_id = int(cursor.lastrowid)
    else:
        switch_controller_id = int(row[0])

    _upsert_component_uuid_map(conn, "switch_controllers", switch_controller_id, controller.uuid)
    switch_controller_id_by_uuid[controller.uuid] = switch_controller_id
    return switch_controller_id


def _write_geometry_branches(conn: sqlite3.Connection, system: DistributionSystem) -> None:
    bus_rows = conn.execute(
        "SELECT id, name, substation_id, feeder_id FROM distribution_buses"
    ).fetchall()
    bus_ref_by_name: dict[str, tuple[int, int, int]] = {
        name: (bus_id, substation_id, feeder_id)
        for bus_id, name, substation_id, feeder_id in bus_rows
    }
    geometry_equipment_id_by_name: dict[str, int] = {}
    bare_conductor_id_by_name: dict[str, int] = {}
    concentric_cable_id_by_name: dict[str, int] = {}

    for branch in system.get_components(GeometryBranch):
        from_bus_id, to_bus_id, substation_id, feeder_id = _resolve_branch_terminal_ids(
            conn,
            bus_ref_by_name,
            branch,
        )
        equipment_id = _upsert_geometry_branch_equipment(
            conn,
            branch.equipment,
            geometry_equipment_id_by_name,
            bare_conductor_id_by_name,
            concentric_cable_id_by_name,
        )

        cursor = conn.execute(
            """
            INSERT INTO geometry_branches(
                name,
                from_bus_id,
                to_bus_id,
                substation_id,
                feeder_id,
                length,
                length_unit,
                equipment_id,
                in_service
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                branch.name,
                from_bus_id,
                to_bus_id,
                substation_id,
                feeder_id,
                float(branch.length.magnitude),
                str(branch.length.units),
                equipment_id,
                1 if branch.in_service else 0,
            ),
        )
        branch_id = int(cursor.lastrowid)
        _upsert_component_uuid_map(conn, "geometry_branches", branch_id, branch.uuid)
        for position_index, phase in enumerate(branch.phases):
            conn.execute(
                "INSERT INTO geometry_branch_phases(branch_id, phase, position_index) VALUES(?, ?, ?)",
                (branch_id, phase.value, position_index),
            )


def _write_matrix_impedance_fuses(conn: sqlite3.Connection, system: DistributionSystem) -> None:
    bus_rows = conn.execute(
        "SELECT id, name, substation_id, feeder_id FROM distribution_buses"
    ).fetchall()
    bus_ref_by_name: dict[str, tuple[int, int, int]] = {
        name: (bus_id, substation_id, feeder_id)
        for bus_id, name, substation_id, feeder_id in bus_rows
    }
    equipment_id_by_name: dict[str, int] = {}
    curve_id_by_uuid: dict[UUID, int] = {}

    for fuse in system.get_components(MatrixImpedanceFuse):
        from_bus_id, to_bus_id, substation_id, feeder_id = _resolve_branch_terminal_ids(
            conn,
            bus_ref_by_name,
            fuse,
        )
        equipment_id = _upsert_matrix_impedance_fuse_equipment(
            conn,
            fuse.equipment,
            equipment_id_by_name,
            curve_id_by_uuid,
        )
        cursor = conn.execute(
            """
            INSERT INTO matrix_impedance_fuses(
                name,
                from_bus_id,
                to_bus_id,
                substation_id,
                feeder_id,
                length,
                length_unit,
                equipment_id,
                in_service
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fuse.name,
                from_bus_id,
                to_bus_id,
                substation_id,
                feeder_id,
                float(fuse.length.magnitude),
                str(fuse.length.units),
                equipment_id,
                1 if fuse.in_service else 0,
            ),
        )
        fuse_id = int(cursor.lastrowid)
        _upsert_component_uuid_map(conn, "matrix_impedance_fuses", fuse_id, fuse.uuid)
        for position_index, phase in enumerate(fuse.phases):
            conn.execute(
                "INSERT INTO matrix_impedance_fuse_phases(fuse_id, phase, position_index) VALUES(?, ?, ?)",
                (fuse_id, phase.value, position_index),
            )
        for position_index, (phase, is_closed) in enumerate(zip(fuse.phases, fuse.is_closed)):
            conn.execute(
                """
                INSERT INTO fuse_phase_states(fuse_id, position_index, phase, is_closed)
                VALUES(?, ?, ?, ?)
                """,
                (fuse_id, position_index, phase.value, 1 if is_closed else 0),
            )


def _upsert_matrix_impedance_fuse_equipment(
    conn: sqlite3.Connection,
    equipment: MatrixImpedanceFuseEquipment,
    equipment_id_by_name: dict[str, int],
    curve_id_by_uuid: dict[UUID, int],
) -> int:
    existing = equipment_id_by_name.get(equipment.name)
    if existing is not None:
        return existing

    row = conn.execute(
        "SELECT id FROM matrix_impedance_fuse_equipment WHERE name = ?",
        (equipment.name,),
    ).fetchone()
    if row is None:
        tcc_curve_id = _upsert_time_current_curve(conn, equipment.tcc_curve, curve_id_by_uuid)
        cursor = conn.execute(
            """
            INSERT INTO matrix_impedance_fuse_equipment(
                name,
                construction,
                ampacity,
                ampacity_unit,
                delay,
                delay_unit,
                tcc_curve_id
            ) VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            (
                equipment.name,
                equipment.construction.value,
                float(equipment.ampacity.magnitude),
                str(equipment.ampacity.units),
                float(equipment.delay.magnitude),
                str(equipment.delay.units),
                tcc_curve_id,
            ),
        )
        equipment_id = int(cursor.lastrowid)
    else:
        equipment_id = int(row[0])

    _upsert_component_uuid_map(
        conn, "matrix_impedance_fuse_equipment", equipment_id, equipment.uuid
    )
    _insert_impedance_matrix_entries(
        conn,
        equipment_id,
        "FUSE",
        "R",
        equipment.r_matrix.magnitude,
        str(equipment.r_matrix.units),
    )
    _insert_impedance_matrix_entries(
        conn,
        equipment_id,
        "FUSE",
        "X",
        equipment.x_matrix.magnitude,
        str(equipment.x_matrix.units),
    )
    _insert_impedance_matrix_entries(
        conn,
        equipment_id,
        "FUSE",
        "C",
        equipment.c_matrix.magnitude,
        str(equipment.c_matrix.units),
    )
    equipment_id_by_name[equipment.name] = equipment_id
    return equipment_id


def _write_matrix_impedance_reclosers(
    conn: sqlite3.Connection, system: DistributionSystem
) -> None:
    bus_rows = conn.execute(
        "SELECT id, name, substation_id, feeder_id FROM distribution_buses"
    ).fetchall()
    bus_ref_by_name: dict[str, tuple[int, int, int]] = {
        name: (bus_id, substation_id, feeder_id)
        for bus_id, name, substation_id, feeder_id in bus_rows
    }
    equipment_id_by_name: dict[str, int] = {}
    controller_id_by_uuid: dict[UUID, int] = {}
    controller_equipment_id_by_name: dict[str, int] = {}
    curve_id_by_uuid: dict[UUID, int] = {}

    for recloser in system.get_components(MatrixImpedanceRecloser):
        from_bus_id, to_bus_id, substation_id, feeder_id = _resolve_branch_terminal_ids(
            conn,
            bus_ref_by_name,
            recloser,
        )
        equipment_id = _upsert_matrix_impedance_recloser_equipment(
            conn,
            recloser.equipment,
            equipment_id_by_name,
        )
        controller_id = _upsert_distribution_recloser_controller(
            conn,
            recloser.controller,
            controller_id_by_uuid,
            controller_equipment_id_by_name,
            curve_id_by_uuid,
        )
        cursor = conn.execute(
            """
            INSERT INTO matrix_impedance_reclosers(
                name,
                from_bus_id,
                to_bus_id,
                substation_id,
                feeder_id,
                length,
                length_unit,
                equipment_id,
                controller_id,
                in_service
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recloser.name,
                from_bus_id,
                to_bus_id,
                substation_id,
                feeder_id,
                float(recloser.length.magnitude),
                str(recloser.length.units),
                equipment_id,
                controller_id,
                1 if recloser.in_service else 0,
            ),
        )
        recloser_id = int(cursor.lastrowid)
        _upsert_component_uuid_map(
            conn,
            "matrix_impedance_reclosers",
            recloser_id,
            recloser.uuid,
        )
        for position_index, phase in enumerate(recloser.phases):
            conn.execute(
                """
                INSERT INTO matrix_impedance_recloser_phases(recloser_id, phase, position_index)
                VALUES(?, ?, ?)
                """,
                (recloser_id, phase.value, position_index),
            )
        for position_index, (phase, is_closed) in enumerate(
            zip(recloser.phases, recloser.is_closed)
        ):
            conn.execute(
                """
                INSERT INTO recloser_phase_states(recloser_id, position_index, phase, is_closed)
                VALUES(?, ?, ?, ?)
                """,
                (recloser_id, position_index, phase.value, 1 if is_closed else 0),
            )


def _upsert_matrix_impedance_recloser_equipment(
    conn: sqlite3.Connection,
    equipment: MatrixImpedanceRecloserEquipment,
    equipment_id_by_name: dict[str, int],
) -> int:
    existing = equipment_id_by_name.get(equipment.name)
    if existing is not None:
        return existing

    row = conn.execute(
        "SELECT id FROM matrix_impedance_recloser_equipment WHERE name = ?",
        (equipment.name,),
    ).fetchone()
    if row is None:
        cursor = conn.execute(
            """
            INSERT INTO matrix_impedance_recloser_equipment(
                name,
                construction,
                ampacity,
                ampacity_unit
            ) VALUES(?, ?, ?, ?)
            """,
            (
                equipment.name,
                equipment.construction.value,
                float(equipment.ampacity.magnitude),
                str(equipment.ampacity.units),
            ),
        )
        equipment_id = int(cursor.lastrowid)
    else:
        equipment_id = int(row[0])

    _upsert_component_uuid_map(
        conn,
        "matrix_impedance_recloser_equipment",
        equipment_id,
        equipment.uuid,
    )
    _insert_impedance_matrix_entries(
        conn,
        equipment_id,
        "RECLOSER",
        "R",
        equipment.r_matrix.magnitude,
        str(equipment.r_matrix.units),
    )
    _insert_impedance_matrix_entries(
        conn,
        equipment_id,
        "RECLOSER",
        "X",
        equipment.x_matrix.magnitude,
        str(equipment.x_matrix.units),
    )
    _insert_impedance_matrix_entries(
        conn,
        equipment_id,
        "RECLOSER",
        "C",
        equipment.c_matrix.magnitude,
        str(equipment.c_matrix.units),
    )
    equipment_id_by_name[equipment.name] = equipment_id
    return equipment_id
