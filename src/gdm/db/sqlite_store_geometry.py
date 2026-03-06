"""Geometry branch helpers for SQLite GDM persistence."""

from __future__ import annotations

import sqlite3

from gdm.db.sqlite_store_identity import _fetch_component_uuid, _upsert_component_uuid_map
from gdm.distribution import DistributionSystem
from gdm.distribution.components import DistributionBus, GeometryBranch
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.enums import Phase, WireInsulationType
from gdm.distribution.equipment.bare_conductor_equipment import BareConductorEquipment
from gdm.distribution.equipment.concentric_cable_equipment import ConcentricCableEquipment
from gdm.distribution.equipment.geometry_branch_equipment import GeometryBranchEquipment
from gdm.quantities import Current, Distance, ResistancePULength, Voltage


def _upsert_bare_conductor_equipment(
    conn: sqlite3.Connection,
    conductor: BareConductorEquipment,
    conductor_id_by_name: dict[str, int],
) -> int:
    existing = conductor_id_by_name.get(conductor.name)
    if existing is not None:
        return existing

    row = conn.execute(
        "SELECT id FROM bare_conductor_equipment WHERE name = ?",
        (conductor.name,),
    ).fetchone()
    if row is None:
        cursor = conn.execute(
            """
            INSERT INTO bare_conductor_equipment(
                name,
                conductor_diameter,
                conductor_diameter_unit,
                conductor_gmr,
                conductor_gmr_unit,
                ampacity,
                ampacity_unit,
                emergency_ampacity,
                emergency_ampacity_unit,
                ac_resistance,
                ac_resistance_unit,
                dc_resistance,
                dc_resistance_unit
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conductor.name,
                float(conductor.conductor_diameter.magnitude),
                str(conductor.conductor_diameter.units),
                float(conductor.conductor_gmr.magnitude),
                str(conductor.conductor_gmr.units),
                float(conductor.ampacity.magnitude),
                str(conductor.ampacity.units),
                float(conductor.emergency_ampacity.magnitude),
                str(conductor.emergency_ampacity.units),
                float(conductor.ac_resistance.magnitude),
                str(conductor.ac_resistance.units),
                float(conductor.dc_resistance.magnitude),
                str(conductor.dc_resistance.units),
            ),
        )
        conductor_id = int(cursor.lastrowid)
    else:
        conductor_id = int(row[0])

    _upsert_component_uuid_map(conn, "bare_conductor_equipment", conductor_id, conductor.uuid)
    conductor_id_by_name[conductor.name] = conductor_id
    return conductor_id


def _upsert_concentric_cable_equipment(
    conn: sqlite3.Connection,
    conductor: ConcentricCableEquipment,
    conductor_id_by_name: dict[str, int],
) -> int:
    existing = conductor_id_by_name.get(conductor.name)
    if existing is not None:
        return existing

    row = conn.execute(
        "SELECT id FROM concentric_cable_equipment WHERE name = ?",
        (conductor.name,),
    ).fetchone()
    if row is None:
        cursor = conn.execute(
            """
            INSERT INTO concentric_cable_equipment(
                name,
                strand_diameter,
                strand_diameter_unit,
                conductor_diameter,
                conductor_diameter_unit,
                cable_diameter,
                cable_diameter_unit,
                insulation_thickness,
                insulation_thickness_unit,
                insulation_diameter,
                insulation_diameter_unit,
                ampacity,
                ampacity_unit,
                conductor_gmr,
                conductor_gmr_unit,
                strand_gmr,
                strand_gmr_unit,
                phase_ac_resistance,
                phase_ac_resistance_unit,
                strand_ac_resistance,
                strand_ac_resistance_unit,
                num_neutral_strands,
                rated_voltage,
                rated_voltage_unit,
                insulation
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conductor.name,
                float(conductor.strand_diameter.magnitude),
                str(conductor.strand_diameter.units),
                float(conductor.conductor_diameter.magnitude),
                str(conductor.conductor_diameter.units),
                float(conductor.cable_diameter.magnitude),
                str(conductor.cable_diameter.units),
                float(conductor.insulation_thickness.magnitude),
                str(conductor.insulation_thickness.units),
                float(conductor.insulation_diameter.magnitude),
                str(conductor.insulation_diameter.units),
                float(conductor.ampacity.magnitude),
                str(conductor.ampacity.units),
                float(conductor.conductor_gmr.magnitude),
                str(conductor.conductor_gmr.units),
                float(conductor.strand_gmr.magnitude),
                str(conductor.strand_gmr.units),
                float(conductor.phase_ac_resistance.magnitude),
                str(conductor.phase_ac_resistance.units),
                float(conductor.strand_ac_resistance.magnitude),
                str(conductor.strand_ac_resistance.units),
                conductor.num_neutral_strands,
                float(conductor.rated_voltage.magnitude),
                str(conductor.rated_voltage.units),
                conductor.insulation.name,
            ),
        )
        conductor_id = int(cursor.lastrowid)
    else:
        conductor_id = int(row[0])

    _upsert_component_uuid_map(conn, "concentric_cable_equipment", conductor_id, conductor.uuid)
    conductor_id_by_name[conductor.name] = conductor_id
    return conductor_id


def _upsert_geometry_branch_equipment(
    conn: sqlite3.Connection,
    equipment: GeometryBranchEquipment,
    geometry_equipment_id_by_name: dict[str, int],
    bare_conductor_id_by_name: dict[str, int],
    concentric_cable_id_by_name: dict[str, int],
) -> int:
    existing = geometry_equipment_id_by_name.get(equipment.name)
    if existing is not None:
        return existing

    row = conn.execute(
        "SELECT id FROM geometry_branch_equipment WHERE name = ?",
        (equipment.name,),
    ).fetchone()
    if row is None:
        cursor = conn.execute(
            "INSERT INTO geometry_branch_equipment(name, insulation) VALUES(?, ?)",
            (equipment.name, equipment.insulation.name),
        )
        equipment_id = int(cursor.lastrowid)
    else:
        equipment_id = int(row[0])

    _upsert_component_uuid_map(conn, "geometry_branch_equipment", equipment_id, equipment.uuid)
    geometry_equipment_id_by_name[equipment.name] = equipment_id

    for position_index, conductor in enumerate(equipment.conductors):
        if isinstance(conductor, BareConductorEquipment):
            bare_id = _upsert_bare_conductor_equipment(conn, conductor, bare_conductor_id_by_name)
            concentric_id = None
        elif isinstance(conductor, ConcentricCableEquipment):
            bare_id = None
            concentric_id = _upsert_concentric_cable_equipment(
                conn,
                conductor,
                concentric_cable_id_by_name,
            )
        else:
            raise TypeError(f"Unsupported geometry conductor type {type(conductor)}")

        conn.execute(
            """
            INSERT INTO geometry_branch_conductors(
                equipment_id,
                position_index,
                horizontal_position,
                horizontal_position_unit,
                vertical_position,
                vertical_position_unit,
                bare_conductor_id,
                concentric_cable_id
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                equipment_id,
                position_index,
                float(equipment.horizontal_positions[position_index].magnitude),
                str(equipment.horizontal_positions.units),
                float(equipment.vertical_positions[position_index].magnitude),
                str(equipment.vertical_positions.units),
                bare_id,
                concentric_id,
            ),
        )

    return equipment_id


def _load_geometry_branches_from_normalized(
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
        FROM geometry_branches
        ORDER BY id
        """
    ).fetchall()
    if not rows:
        return

    bare_cache: dict[int, BareConductorEquipment] = {}
    concentric_cache: dict[int, ConcentricCableEquipment] = {}
    equipment_cache: dict[int, GeometryBranchEquipment] = {}

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
                "SELECT name, insulation FROM geometry_branch_equipment WHERE id = ?",
                (equipment_id,),
            ).fetchone()
            if equipment_row is None:
                raise ValueError(f"geometry_branch_equipment_id={equipment_id} not found")

            conductor_rows = conn.execute(
                """
                SELECT
                    position_index,
                    horizontal_position,
                    horizontal_position_unit,
                    vertical_position,
                    vertical_position_unit,
                    bare_conductor_id,
                    concentric_cable_id
                FROM geometry_branch_conductors
                WHERE equipment_id = ?
                ORDER BY position_index
                """,
                (equipment_id,),
            ).fetchall()

            conductors: list[BareConductorEquipment | ConcentricCableEquipment] = []
            horizontal_values: list[float] = []
            vertical_values: list[float] = []
            horizontal_unit = "meter"
            vertical_unit = "meter"

            for (
                _,
                horizontal_position,
                horizontal_position_unit,
                vertical_position,
                vertical_position_unit,
                bare_conductor_id,
                concentric_cable_id,
            ) in conductor_rows:
                horizontal_values.append(horizontal_position)
                vertical_values.append(vertical_position)
                horizontal_unit = horizontal_position_unit
                vertical_unit = vertical_position_unit

                if bare_conductor_id is not None:
                    conductor = bare_cache.get(bare_conductor_id)
                    if conductor is None:
                        bare_row = conn.execute(
                            """
                            SELECT
                                name,
                                conductor_diameter,
                                conductor_diameter_unit,
                                conductor_gmr,
                                conductor_gmr_unit,
                                ampacity,
                                ampacity_unit,
                                emergency_ampacity,
                                emergency_ampacity_unit,
                                ac_resistance,
                                ac_resistance_unit,
                                dc_resistance,
                                dc_resistance_unit
                            FROM bare_conductor_equipment
                            WHERE id = ?
                            """,
                            (bare_conductor_id,),
                        ).fetchone()
                        if bare_row is None:
                            raise ValueError(
                                f"bare_conductor_equipment_id={bare_conductor_id} not found"
                            )
                        conductor = BareConductorEquipment(
                            name=bare_row[0],
                            conductor_diameter=Distance(bare_row[1], bare_row[2]),
                            conductor_gmr=Distance(bare_row[3], bare_row[4]),
                            ampacity=Current(bare_row[5], bare_row[6]),
                            emergency_ampacity=Current(bare_row[7], bare_row[8]),
                            ac_resistance=ResistancePULength(bare_row[9], bare_row[10]),
                            dc_resistance=ResistancePULength(bare_row[11], bare_row[12]),
                        )
                        conductor_uuid = _fetch_component_uuid(
                            conn,
                            "bare_conductor_equipment",
                            bare_conductor_id,
                        )
                        if conductor_uuid is not None:
                            conductor = conductor.model_copy(update={"uuid": conductor_uuid})
                        bare_cache[bare_conductor_id] = conductor
                    conductors.append(conductor)
                else:
                    conductor = concentric_cache.get(concentric_cable_id)
                    if conductor is None:
                        concentric_row = conn.execute(
                            """
                            SELECT
                                name,
                                strand_diameter,
                                strand_diameter_unit,
                                conductor_diameter,
                                conductor_diameter_unit,
                                cable_diameter,
                                cable_diameter_unit,
                                insulation_thickness,
                                insulation_thickness_unit,
                                insulation_diameter,
                                insulation_diameter_unit,
                                ampacity,
                                ampacity_unit,
                                conductor_gmr,
                                conductor_gmr_unit,
                                strand_gmr,
                                strand_gmr_unit,
                                phase_ac_resistance,
                                phase_ac_resistance_unit,
                                strand_ac_resistance,
                                strand_ac_resistance_unit,
                                num_neutral_strands,
                                rated_voltage,
                                rated_voltage_unit,
                                insulation
                            FROM concentric_cable_equipment
                            WHERE id = ?
                            """,
                            (concentric_cable_id,),
                        ).fetchone()
                        if concentric_row is None:
                            raise ValueError(
                                f"concentric_cable_equipment_id={concentric_cable_id} not found"
                            )
                        conductor = ConcentricCableEquipment(
                            name=concentric_row[0],
                            strand_diameter=Distance(concentric_row[1], concentric_row[2]),
                            conductor_diameter=Distance(concentric_row[3], concentric_row[4]),
                            cable_diameter=Distance(concentric_row[5], concentric_row[6]),
                            insulation_thickness=Distance(concentric_row[7], concentric_row[8]),
                            insulation_diameter=Distance(concentric_row[9], concentric_row[10]),
                            ampacity=Current(concentric_row[11], concentric_row[12]),
                            conductor_gmr=Distance(concentric_row[13], concentric_row[14]),
                            strand_gmr=Distance(concentric_row[15], concentric_row[16]),
                            phase_ac_resistance=ResistancePULength(
                                concentric_row[17],
                                concentric_row[18],
                            ),
                            strand_ac_resistance=ResistancePULength(
                                concentric_row[19],
                                concentric_row[20],
                            ),
                            num_neutral_strands=concentric_row[21],
                            rated_voltage=Voltage(concentric_row[22], concentric_row[23]),
                            insulation=WireInsulationType[concentric_row[24]],
                        )
                        conductor_uuid = _fetch_component_uuid(
                            conn,
                            "concentric_cable_equipment",
                            concentric_cable_id,
                        )
                        if conductor_uuid is not None:
                            conductor = conductor.model_copy(update={"uuid": conductor_uuid})
                        concentric_cache[concentric_cable_id] = conductor
                    conductors.append(conductor)

            equipment = GeometryBranchEquipment(
                name=equipment_row[0],
                insulation=WireInsulationType[equipment_row[1]],
                conductors=conductors,
                horizontal_positions=Distance(horizontal_values, horizontal_unit),
                vertical_positions=Distance(vertical_values, vertical_unit),
            )
            equipment_uuid = _fetch_component_uuid(conn, "geometry_branch_equipment", equipment_id)
            if equipment_uuid is not None:
                equipment = equipment.model_copy(update={"uuid": equipment_uuid})
            equipment_cache[equipment_id] = equipment

        phases_rows = conn.execute(
            "SELECT phase FROM geometry_branch_phases WHERE branch_id = ? ORDER BY position_index",
            (branch_id,),
        ).fetchall()
        branch = GeometryBranch(
            name=name,
            buses=[buses_by_id[from_bus_id], buses_by_id[to_bus_id]],
            substation=substations_by_id[substation_id],
            feeder=feeders_by_id[feeder_id],
            length=Distance(length, length_unit),
            phases=[Phase(phase) for (phase,) in phases_rows],
            equipment=equipment,
            in_service=bool(in_service),
        )
        branch_uuid = _fetch_component_uuid(conn, "geometry_branches", branch_id)
        if branch_uuid is not None:
            branch = branch.model_copy(update={"uuid": branch_uuid})
        system.add_component(branch)
