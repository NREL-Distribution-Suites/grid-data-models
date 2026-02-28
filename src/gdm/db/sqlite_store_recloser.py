"""Recloser controller helpers for SQLite GDM persistence."""

from __future__ import annotations

import sqlite3
from uuid import UUID

from infrasys.quantities import Time

from gdm.db.sqlite_store_controls_curves import (
    _load_time_current_curve,
    _upsert_time_current_curve,
)
from gdm.db.sqlite_store_identity import _fetch_component_uuid, _upsert_component_uuid_map
from gdm.distribution.common.curve import TimeCurrentCurve
from gdm.distribution.controllers.distribution_recloser_controller import (
    DistributionRecloserController,
)
from gdm.distribution.equipment.recloser_controller_equipment import (
    RecloserControllerEquipment,
)


def _upsert_recloser_controller_equipment(
    conn: sqlite3.Connection,
    equipment: RecloserControllerEquipment,
    equipment_id_by_name: dict[str, int],
) -> int:
    existing = equipment_id_by_name.get(equipment.name)
    if existing is not None:
        return existing

    row = conn.execute(
        "SELECT id FROM recloser_controller_equipment WHERE name = ?",
        (equipment.name,),
    ).fetchone()
    if row is None:
        cursor = conn.execute(
            "INSERT INTO recloser_controller_equipment(name) VALUES(?)",
            (equipment.name,),
        )
        equipment_id = int(cursor.lastrowid)
    else:
        equipment_id = int(row[0])

    _upsert_component_uuid_map(
        conn,
        "recloser_controller_equipment",
        equipment_id,
        equipment.uuid,
    )
    equipment_id_by_name[equipment.name] = equipment_id
    return equipment_id


def _upsert_distribution_recloser_controller(
    conn: sqlite3.Connection,
    controller: DistributionRecloserController,
    controller_id_by_uuid: dict[UUID, int],
    equipment_id_by_name: dict[str, int],
    curve_id_by_uuid: dict[UUID, int],
) -> int:
    existing = controller_id_by_uuid.get(controller.uuid)
    if existing is not None:
        return existing

    equipment_id = _upsert_recloser_controller_equipment(
        conn,
        controller.equipment,
        equipment_id_by_name,
    )
    ground_delayed_curve_id = _upsert_time_current_curve(
        conn,
        controller.ground_delayed,
        curve_id_by_uuid,
    )
    ground_fast_curve_id = _upsert_time_current_curve(
        conn,
        controller.ground_fast,
        curve_id_by_uuid,
    )
    phase_delayed_curve_id = _upsert_time_current_curve(
        conn,
        controller.phase_delayed,
        curve_id_by_uuid,
    )
    phase_fast_curve_id = _upsert_time_current_curve(
        conn,
        controller.phase_fast,
        curve_id_by_uuid,
    )

    cursor = conn.execute(
        """
        INSERT INTO recloser_controllers(
            name,
            delay,
            delay_unit,
            ground_delayed_curve_id,
            ground_fast_curve_id,
            phase_delayed_curve_id,
            phase_fast_curve_id,
            num_fast_ops,
            num_shots,
            reset_time,
            reset_time_unit,
            equipment_id
        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            controller.name,
            float(controller.delay.magnitude),
            str(controller.delay.units),
            ground_delayed_curve_id,
            ground_fast_curve_id,
            phase_delayed_curve_id,
            phase_fast_curve_id,
            controller.num_fast_ops,
            controller.num_shots,
            float(controller.reset_time.magnitude),
            str(controller.reset_time.units),
            equipment_id,
        ),
    )
    controller_id = int(cursor.lastrowid)
    _upsert_component_uuid_map(conn, "recloser_controllers", controller_id, controller.uuid)
    for position_index, interval in enumerate(controller.reclose_intervals.magnitude):
        conn.execute(
            """
            INSERT INTO recloser_reclose_intervals(
                recloser_controller_id,
                position_index,
                interval_value,
                interval_unit
            ) VALUES(?, ?, ?, ?)
            """,
            (
                controller_id,
                position_index,
                float(interval),
                str(controller.reclose_intervals.units),
            ),
        )

    controller_id_by_uuid[controller.uuid] = controller_id
    return controller_id


def _load_distribution_recloser_controller(
    conn: sqlite3.Connection,
    controller_id: int,
    controller_cache: dict[int, DistributionRecloserController],
    curve_cache: dict[int, TimeCurrentCurve],
    equipment_cache: dict[int, RecloserControllerEquipment],
) -> DistributionRecloserController:
    cached = controller_cache.get(controller_id)
    if cached is not None:
        return cached

    row = conn.execute(
        """
        SELECT
            name,
            delay,
            delay_unit,
            ground_delayed_curve_id,
            ground_fast_curve_id,
            phase_delayed_curve_id,
            phase_fast_curve_id,
            num_fast_ops,
            num_shots,
            reset_time,
            reset_time_unit,
            equipment_id
        FROM recloser_controllers
        WHERE id = ?
        """,
        (controller_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"recloser_controller_id={controller_id} not found")

    equipment = equipment_cache.get(row[11])
    if equipment is None:
        equipment_row = conn.execute(
            "SELECT name FROM recloser_controller_equipment WHERE id = ?",
            (row[11],),
        ).fetchone()
        if equipment_row is None:
            raise ValueError(f"recloser_controller_equipment_id={row[11]} not found")
        equipment = RecloserControllerEquipment(name=equipment_row[0])
        equipment_uuid = _fetch_component_uuid(conn, "recloser_controller_equipment", row[11])
        if equipment_uuid is not None:
            equipment = equipment.model_copy(update={"uuid": equipment_uuid})
        equipment_cache[row[11]] = equipment

    interval_rows = conn.execute(
        """
        SELECT interval_value, interval_unit
        FROM recloser_reclose_intervals
        WHERE recloser_controller_id = ?
        ORDER BY position_index
        """,
        (controller_id,),
    ).fetchall()
    interval_unit = interval_rows[0][1] if interval_rows else "second"
    reclose_values = [interval for interval, _ in interval_rows]

    controller = DistributionRecloserController(
        name=row[0],
        delay=Time(row[1], row[2]),
        ground_delayed=_load_time_current_curve(conn, row[3], curve_cache),
        ground_fast=_load_time_current_curve(conn, row[4], curve_cache),
        phase_delayed=_load_time_current_curve(conn, row[5], curve_cache),
        phase_fast=_load_time_current_curve(conn, row[6], curve_cache),
        num_fast_ops=row[7],
        num_shots=row[8],
        reclose_intervals=Time(reclose_values, interval_unit),
        reset_time=Time(row[9], row[10]),
        equipment=equipment,
    )
    controller_uuid = _fetch_component_uuid(conn, "recloser_controllers", controller_id)
    if controller_uuid is not None:
        controller = controller.model_copy(update={"uuid": controller_uuid})
    controller_cache[controller_id] = controller
    return controller
