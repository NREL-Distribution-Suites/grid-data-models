"""Matrix/sequence branch read-write helpers for SQLite GDM persistence."""

from __future__ import annotations

import sqlite3

from gdm.db.sqlite_store_identity import _fetch_component_uuid, _upsert_component_uuid_map
from gdm.db.sqlite_store_impedance import _insert_impedance_matrix_entries, _load_impedance_matrix
from gdm.distribution import DistributionSystem
from gdm.distribution.components import (
    DistributionBus,
    MatrixImpedanceBranch,
    SequenceImpedanceBranch,
)
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.enums import LineType, Phase
from gdm.distribution.equipment.matrix_impedance_branch_equipment import (
    MatrixImpedanceBranchEquipment,
)
from gdm.distribution.equipment.sequence_impedance_branch_equipment import (
    SequenceImpedanceBranchEquipment,
)
from gdm.quantities import (
    CapacitancePULength,
    Current,
    Distance,
    ReactancePULength,
    ResistancePULength,
)


def _write_matrix_impedance_branches(conn: sqlite3.Connection, system: DistributionSystem) -> None:
    bus_rows = conn.execute(
        "SELECT id, name, substation_id, feeder_id FROM distribution_buses"
    ).fetchall()
    bus_ref_by_name: dict[str, tuple[int, int, int]] = {
        name: (bus_id, substation_id, feeder_id)
        for bus_id, name, substation_id, feeder_id in bus_rows
    }
    matrix_equipment_id_by_name: dict[str, int] = {}

    for branch in system.get_components(MatrixImpedanceBranch):
        from_bus_ref = bus_ref_by_name.get(branch.buses[0].name)
        to_bus_ref = bus_ref_by_name.get(branch.buses[1].name)
        if from_bus_ref is None or to_bus_ref is None:
            raise ValueError(f"MatrixImpedanceBranch '{branch.name}' references unknown buses")

        from_bus_id, from_substation_id, from_feeder_id = from_bus_ref
        to_bus_id, _, _ = to_bus_ref

        substation_id: int | None = None
        feeder_id: int | None = None
        if branch.substation is not None:
            row = conn.execute(
                "SELECT id FROM distribution_substations WHERE name = ?",
                (branch.substation.name,),
            ).fetchone()
            substation_id = int(row[0]) if row is not None else None
        if branch.feeder is not None:
            row = conn.execute(
                "SELECT id FROM distribution_feeders WHERE name = ?",
                (branch.feeder.name,),
            ).fetchone()
            feeder_id = int(row[0]) if row is not None else None

        if substation_id is None:
            substation_id = from_substation_id
        if feeder_id is None:
            feeder_id = from_feeder_id

        equipment_id = _upsert_matrix_impedance_branch_equipment(
            conn,
            branch.equipment,
            matrix_equipment_id_by_name,
        )

        cursor = conn.execute(
            """
            INSERT INTO matrix_impedance_branches(
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
        _upsert_component_uuid_map(conn, "matrix_impedance_branches", branch_id, branch.uuid)

        for position_index, phase in enumerate(branch.phases):
            conn.execute(
                """
                INSERT INTO matrix_impedance_branch_phases(branch_id, phase, position_index)
                VALUES(?, ?, ?)
                """,
                (branch_id, phase.value, position_index),
            )


def _upsert_matrix_impedance_branch_equipment(
    conn: sqlite3.Connection,
    equipment: MatrixImpedanceBranchEquipment,
    equipment_id_by_name: dict[str, int],
) -> int:
    existing = equipment_id_by_name.get(equipment.name)
    if existing is not None:
        return existing

    row = conn.execute(
        "SELECT id FROM matrix_impedance_branch_equipment WHERE name = ?",
        (equipment.name,),
    ).fetchone()
    if row is not None:
        equipment_id = int(row[0])
        equipment_id_by_name[equipment.name] = equipment_id
        return equipment_id

    cursor = conn.execute(
        """
        INSERT INTO matrix_impedance_branch_equipment(
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
    _upsert_component_uuid_map(
        conn,
        "matrix_impedance_branch_equipment",
        equipment_id,
        equipment.uuid,
    )

    _insert_impedance_matrix_entries(
        conn,
        equipment_id,
        "LINE",
        "R",
        equipment.r_matrix.magnitude,
        str(equipment.r_matrix.units),
    )
    _insert_impedance_matrix_entries(
        conn,
        equipment_id,
        "LINE",
        "X",
        equipment.x_matrix.magnitude,
        str(equipment.x_matrix.units),
    )
    _insert_impedance_matrix_entries(
        conn,
        equipment_id,
        "LINE",
        "C",
        equipment.c_matrix.magnitude,
        str(equipment.c_matrix.units),
    )

    equipment_id_by_name[equipment.name] = equipment_id
    return equipment_id


def _load_matrix_impedance_branches_from_normalized(
    conn: sqlite3.Connection,
    system: DistributionSystem,
    buses_by_id: dict[int, DistributionBus],
    substations_by_id: dict[int, DistributionSubstation],
    feeders_by_id: dict[int, DistributionFeeder],
) -> None:
    branch_rows = conn.execute(
        """
        SELECT
            id,
            name,
            from_bus_id,
            to_bus_id,
            substation_id,
            feeder_id,
            length,
            length_unit,
            equipment_id,
            in_service
        FROM matrix_impedance_branches
        ORDER BY id
        """
    ).fetchall()
    if not branch_rows:
        return

    equipment_cache: dict[int, MatrixImpedanceBranchEquipment] = {}

    for (
        branch_id,
        name,
        from_bus_id,
        to_bus_id,
        substation_id,
        feeder_id,
        length,
        length_unit,
        equipment_id,
        in_service,
    ) in branch_rows:
        equipment = equipment_cache.get(equipment_id)
        if equipment is None:
            equipment_header = conn.execute(
                """
                SELECT name, construction, ampacity, ampacity_unit
                FROM matrix_impedance_branch_equipment
                WHERE id = ?
                """,
                (equipment_id,),
            ).fetchone()
            if equipment_header is None:
                raise ValueError(f"matrix_impedance_branch_equipment_id={equipment_id} not found")
            (
                equipment_name,
                construction,
                ampacity,
                ampacity_unit,
            ) = equipment_header

            r_matrix, r_unit = _load_impedance_matrix(conn, equipment_id, "LINE", "R")
            x_matrix, x_unit = _load_impedance_matrix(conn, equipment_id, "LINE", "X")
            c_matrix, c_unit = _load_impedance_matrix(conn, equipment_id, "LINE", "C")

            equipment = MatrixImpedanceBranchEquipment(
                name=equipment_name,
                construction=LineType(construction),
                r_matrix=ResistancePULength(r_matrix, r_unit),
                x_matrix=ReactancePULength(x_matrix, x_unit),
                c_matrix=CapacitancePULength(c_matrix, c_unit),
                ampacity=Current(ampacity, ampacity_unit),
            )
            equipment_uuid = _fetch_component_uuid(
                conn,
                "matrix_impedance_branch_equipment",
                equipment_id,
            )
            if equipment_uuid is not None:
                equipment = equipment.model_copy(update={"uuid": equipment_uuid})
            equipment_cache[equipment_id] = equipment

        phases_rows = conn.execute(
            """
            SELECT phase
            FROM matrix_impedance_branch_phases
            WHERE branch_id = ?
            ORDER BY position_index
            """,
            (branch_id,),
        ).fetchall()

        branch = MatrixImpedanceBranch(
            name=name,
            buses=[buses_by_id[from_bus_id], buses_by_id[to_bus_id]],
            substation=substations_by_id[substation_id],
            feeder=feeders_by_id[feeder_id],
            length=Distance(length, length_unit),
            phases=[Phase(phase) for (phase,) in phases_rows],
            equipment=equipment,
            in_service=bool(in_service),
        )
        branch_uuid = _fetch_component_uuid(conn, "matrix_impedance_branches", branch_id)
        if branch_uuid is not None:
            branch = branch.model_copy(update={"uuid": branch_uuid})
        system.add_component(branch)


def _write_sequence_impedance_branches(
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

    for branch in system.get_components(SequenceImpedanceBranch):
        from_bus_ref = bus_ref_by_name.get(branch.buses[0].name)
        to_bus_ref = bus_ref_by_name.get(branch.buses[1].name)
        if from_bus_ref is None or to_bus_ref is None:
            raise ValueError(f"SequenceImpedanceBranch '{branch.name}' references unknown buses")

        from_bus_id, from_substation_id, from_feeder_id = from_bus_ref
        to_bus_id, _, _ = to_bus_ref

        substation_id: int | None = None
        feeder_id: int | None = None
        if branch.substation is not None:
            row = conn.execute(
                "SELECT id FROM distribution_substations WHERE name = ?",
                (branch.substation.name,),
            ).fetchone()
            substation_id = int(row[0]) if row is not None else None
        if branch.feeder is not None:
            row = conn.execute(
                "SELECT id FROM distribution_feeders WHERE name = ?",
                (branch.feeder.name,),
            ).fetchone()
            feeder_id = int(row[0]) if row is not None else None

        if substation_id is None:
            substation_id = from_substation_id
        if feeder_id is None:
            feeder_id = from_feeder_id

        equipment_id = _upsert_sequence_impedance_branch_equipment(
            conn,
            branch.equipment,
            equipment_id_by_name,
        )

        cursor = conn.execute(
            """
            INSERT INTO sequence_impedance_branches(
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
        _upsert_component_uuid_map(conn, "sequence_impedance_branches", branch_id, branch.uuid)

        for position_index, phase in enumerate(branch.phases):
            conn.execute(
                """
                INSERT INTO sequence_impedance_branch_phases(branch_id, phase, position_index)
                VALUES(?, ?, ?)
                """,
                (branch_id, phase.value, position_index),
            )


def _upsert_sequence_impedance_branch_equipment(
    conn: sqlite3.Connection,
    equipment: SequenceImpedanceBranchEquipment,
    equipment_id_by_name: dict[str, int],
) -> int:
    existing = equipment_id_by_name.get(equipment.name)
    if existing is not None:
        return existing

    row = conn.execute(
        "SELECT id FROM sequence_impedance_branch_equipment WHERE name = ?",
        (equipment.name,),
    ).fetchone()
    if row is not None:
        equipment_id = int(row[0])
        equipment_id_by_name[equipment.name] = equipment_id
        return equipment_id

    cursor = conn.execute(
        """
        INSERT INTO sequence_impedance_branch_equipment(
            name,
            pos_seq_resistance,
            pos_seq_resistance_unit,
            zero_seq_resistance,
            zero_seq_resistance_unit,
            pos_seq_reactance,
            pos_seq_reactance_unit,
            zero_seq_reactance,
            zero_seq_reactance_unit,
            pos_seq_capacitance,
            pos_seq_capacitance_unit,
            zero_seq_capacitance,
            zero_seq_capacitance_unit,
            ampacity,
            ampacity_unit
        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            equipment.name,
            float(equipment.pos_seq_resistance.magnitude),
            str(equipment.pos_seq_resistance.units),
            float(equipment.zero_seq_resistance.magnitude),
            str(equipment.zero_seq_resistance.units),
            float(equipment.pos_seq_reactance.magnitude),
            str(equipment.pos_seq_reactance.units),
            float(equipment.zero_seq_reactance.magnitude),
            str(equipment.zero_seq_reactance.units),
            float(equipment.pos_seq_capacitance.magnitude),
            str(equipment.pos_seq_capacitance.units),
            float(equipment.zero_seq_capacitance.magnitude),
            str(equipment.zero_seq_capacitance.units),
            float(equipment.ampacity.magnitude),
            str(equipment.ampacity.units),
        ),
    )
    equipment_id = int(cursor.lastrowid)
    _upsert_component_uuid_map(
        conn,
        "sequence_impedance_branch_equipment",
        equipment_id,
        equipment.uuid,
    )
    equipment_id_by_name[equipment.name] = equipment_id
    return equipment_id


def _load_sequence_impedance_branches_from_normalized(
    conn: sqlite3.Connection,
    system: DistributionSystem,
    buses_by_id: dict[int, DistributionBus],
    substations_by_id: dict[int, DistributionSubstation],
    feeders_by_id: dict[int, DistributionFeeder],
) -> None:
    rows = conn.execute(
        """
        SELECT
            id,
            name,
            from_bus_id,
            to_bus_id,
            substation_id,
            feeder_id,
            length,
            length_unit,
            equipment_id,
            in_service
        FROM sequence_impedance_branches
        ORDER BY id
        """
    ).fetchall()
    if not rows:
        return

    equipment_cache: dict[int, SequenceImpedanceBranchEquipment] = {}

    for (
        branch_id,
        name,
        from_bus_id,
        to_bus_id,
        substation_id,
        feeder_id,
        length,
        length_unit,
        equipment_id,
        in_service,
    ) in rows:
        equipment = equipment_cache.get(equipment_id)
        if equipment is None:
            equipment_row = conn.execute(
                """
                SELECT
                    name,
                    pos_seq_resistance,
                    pos_seq_resistance_unit,
                    zero_seq_resistance,
                    zero_seq_resistance_unit,
                    pos_seq_reactance,
                    pos_seq_reactance_unit,
                    zero_seq_reactance,
                    zero_seq_reactance_unit,
                    pos_seq_capacitance,
                    pos_seq_capacitance_unit,
                    zero_seq_capacitance,
                    zero_seq_capacitance_unit,
                    ampacity,
                    ampacity_unit
                FROM sequence_impedance_branch_equipment
                WHERE id = ?
                """,
                (equipment_id,),
            ).fetchone()
            if equipment_row is None:
                raise ValueError(
                    f"sequence_impedance_branch_equipment_id={equipment_id} not found"
                )

            equipment = SequenceImpedanceBranchEquipment(
                name=equipment_row[0],
                pos_seq_resistance=ResistancePULength(equipment_row[1], equipment_row[2]),
                zero_seq_resistance=ResistancePULength(equipment_row[3], equipment_row[4]),
                pos_seq_reactance=ReactancePULength(equipment_row[5], equipment_row[6]),
                zero_seq_reactance=ReactancePULength(equipment_row[7], equipment_row[8]),
                pos_seq_capacitance=CapacitancePULength(equipment_row[9], equipment_row[10]),
                zero_seq_capacitance=CapacitancePULength(equipment_row[11], equipment_row[12]),
                ampacity=Current(equipment_row[13], equipment_row[14]),
            )
            equipment_uuid = _fetch_component_uuid(
                conn,
                "sequence_impedance_branch_equipment",
                equipment_id,
            )
            if equipment_uuid is not None:
                equipment = equipment.model_copy(update={"uuid": equipment_uuid})
            equipment_cache[equipment_id] = equipment

        phases = conn.execute(
            """
            SELECT phase
            FROM sequence_impedance_branch_phases
            WHERE branch_id = ?
            ORDER BY position_index
            """,
            (branch_id,),
        ).fetchall()

        branch = SequenceImpedanceBranch(
            name=name,
            buses=[buses_by_id[from_bus_id], buses_by_id[to_bus_id]],
            substation=substations_by_id[substation_id],
            feeder=feeders_by_id[feeder_id],
            length=Distance(length, length_unit),
            phases=[Phase(phase) for (phase,) in phases],
            equipment=equipment,
            in_service=bool(in_service),
        )
        branch_uuid = _fetch_component_uuid(conn, "sequence_impedance_branches", branch_id)
        if branch_uuid is not None:
            branch = branch.model_copy(update={"uuid": branch_uuid})
        system.add_component(branch)
