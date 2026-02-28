"""Normalized switchgear loader helpers for SQLite GDM persistence."""

from __future__ import annotations

import sqlite3

from infrasys.quantities import Time

from gdm.db.sqlite_store_controls_curves import _load_time_current_curve
from gdm.db.sqlite_store_identity import _fetch_component_uuid
from gdm.db.sqlite_store_impedance import _load_impedance_matrix
from gdm.db.sqlite_store_recloser import _load_distribution_recloser_controller
from gdm.distribution import DistributionSystem
from gdm.distribution.components import (
    DistributionBus,
    MatrixImpedanceFuse,
    MatrixImpedanceRecloser,
    MatrixImpedanceSwitch,
)
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.controllers.distribution_recloser_controller import (
    DistributionRecloserController,
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
from gdm.distribution.equipment.recloser_controller_equipment import (
    RecloserControllerEquipment,
)
from gdm.distribution.common.curve import TimeCurrentCurve
from gdm.distribution.enums import LineType, Phase
from gdm.quantities import (
    CapacitancePULength,
    Current,
    Distance,
    ReactancePULength,
    ResistancePULength,
)


def _load_matrix_impedance_switches_from_normalized(
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
        FROM matrix_impedance_switches
        ORDER BY id
        """
    ).fetchall()
    if not rows:
        return

    equipment_cache: dict[int, MatrixImpedanceSwitchEquipment] = {}

    for (
        switch_id,
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
            equipment_header = conn.execute(
                """
                SELECT name, construction, ampacity, ampacity_unit, switch_controller_id
                FROM matrix_impedance_switch_equipment
                WHERE id = ?
                """,
                (equipment_id,),
            ).fetchone()
            if equipment_header is None:
                raise ValueError(f"matrix_impedance_switch_equipment_id={equipment_id} not found")

            (
                equipment_name,
                construction,
                ampacity,
                ampacity_unit,
                switch_controller_id,
            ) = equipment_header

            controller: DistributionSwitchController | None = None
            if switch_controller_id is not None:
                controller_row = conn.execute(
                    """
                    SELECT name, delay, delay_unit, normal_state, is_locked
                    FROM switch_controllers
                    WHERE id = ?
                    """,
                    (switch_controller_id,),
                ).fetchone()
                if controller_row is None:
                    raise ValueError(f"switch_controller_id={switch_controller_id} not found")
                controller = DistributionSwitchController(
                    name=controller_row[0],
                    delay=Time(controller_row[1], controller_row[2]),
                    normal_state=controller_row[3],
                    is_locked=bool(controller_row[4]),
                )
                controller_uuid = _fetch_component_uuid(
                    conn,
                    "switch_controllers",
                    switch_controller_id,
                )
                if controller_uuid is not None:
                    controller = controller.model_copy(update={"uuid": controller_uuid})

            r_matrix, r_unit = _load_impedance_matrix(conn, equipment_id, "SWITCH", "R")
            x_matrix, x_unit = _load_impedance_matrix(conn, equipment_id, "SWITCH", "X")
            c_matrix, c_unit = _load_impedance_matrix(conn, equipment_id, "SWITCH", "C")

            equipment = MatrixImpedanceSwitchEquipment(
                name=equipment_name,
                construction=LineType(construction),
                r_matrix=ResistancePULength(r_matrix, r_unit),
                x_matrix=ReactancePULength(x_matrix, x_unit),
                c_matrix=CapacitancePULength(c_matrix, c_unit),
                ampacity=Current(ampacity, ampacity_unit),
                controller=controller,
            )
            equipment_uuid = _fetch_component_uuid(
                conn,
                "matrix_impedance_switch_equipment",
                equipment_id,
            )
            if equipment_uuid is not None:
                equipment = equipment.model_copy(update={"uuid": equipment_uuid})
            equipment_cache[equipment_id] = equipment

        phases_rows = conn.execute(
            """
            SELECT phase
            FROM matrix_impedance_switch_phases
            WHERE switch_id = ?
            ORDER BY position_index
            """,
            (switch_id,),
        ).fetchall()
        phases = [Phase(phase) for (phase,) in phases_rows]

        state_rows = conn.execute(
            """
            SELECT is_closed
            FROM switch_phase_states
            WHERE switch_id = ?
            ORDER BY position_index
            """,
            (switch_id,),
        ).fetchall()
        is_closed = [bool(state) for (state,) in state_rows]

        switch = MatrixImpedanceSwitch(
            name=name,
            buses=[buses_by_id[from_bus_id], buses_by_id[to_bus_id]],
            substation=substations_by_id[substation_id],
            feeder=feeders_by_id[feeder_id],
            length=Distance(length, length_unit),
            phases=phases,
            is_closed=is_closed,
            equipment=equipment,
            in_service=bool(in_service),
        )
        switch_uuid = _fetch_component_uuid(conn, "matrix_impedance_switches", switch_id)
        if switch_uuid is not None:
            switch = switch.model_copy(update={"uuid": switch_uuid})
        system.add_component(switch)


def _load_matrix_impedance_fuses_from_normalized(
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
        FROM matrix_impedance_fuses
        ORDER BY id
        """
    ).fetchall()
    if not rows:
        return

    equipment_cache: dict[int, MatrixImpedanceFuseEquipment] = {}
    curve_cache: dict[int, TimeCurrentCurve] = {}

    for (
        fuse_id,
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
                    construction,
                    ampacity,
                    ampacity_unit,
                    delay,
                    delay_unit,
                    tcc_curve_id
                FROM matrix_impedance_fuse_equipment
                WHERE id = ?
                """,
                (equipment_id,),
            ).fetchone()
            if equipment_row is None:
                raise ValueError(f"matrix_impedance_fuse_equipment_id={equipment_id} not found")

            r_matrix, r_unit = _load_impedance_matrix(conn, equipment_id, "FUSE", "R")
            x_matrix, x_unit = _load_impedance_matrix(conn, equipment_id, "FUSE", "X")
            c_matrix, c_unit = _load_impedance_matrix(conn, equipment_id, "FUSE", "C")

            equipment = MatrixImpedanceFuseEquipment(
                name=equipment_row[0],
                construction=LineType(equipment_row[1]),
                ampacity=Current(equipment_row[2], equipment_row[3]),
                delay=Time(equipment_row[4], equipment_row[5]),
                tcc_curve=_load_time_current_curve(conn, equipment_row[6], curve_cache),
                r_matrix=ResistancePULength(r_matrix, r_unit),
                x_matrix=ReactancePULength(x_matrix, x_unit),
                c_matrix=CapacitancePULength(c_matrix, c_unit),
            )
            equipment_uuid = _fetch_component_uuid(
                conn,
                "matrix_impedance_fuse_equipment",
                equipment_id,
            )
            if equipment_uuid is not None:
                equipment = equipment.model_copy(update={"uuid": equipment_uuid})
            equipment_cache[equipment_id] = equipment

        phases_rows = conn.execute(
            "SELECT phase FROM matrix_impedance_fuse_phases WHERE fuse_id = ? ORDER BY position_index",
            (fuse_id,),
        ).fetchall()
        state_rows = conn.execute(
            "SELECT is_closed FROM fuse_phase_states WHERE fuse_id = ? ORDER BY position_index",
            (fuse_id,),
        ).fetchall()
        fuse = MatrixImpedanceFuse(
            name=name,
            buses=[buses_by_id[from_bus_id], buses_by_id[to_bus_id]],
            substation=substations_by_id[substation_id],
            feeder=feeders_by_id[feeder_id],
            length=Distance(length, length_unit),
            phases=[Phase(phase) for (phase,) in phases_rows],
            is_closed=[bool(state) for (state,) in state_rows],
            equipment=equipment,
            in_service=bool(in_service),
        )
        fuse_uuid = _fetch_component_uuid(conn, "matrix_impedance_fuses", fuse_id)
        if fuse_uuid is not None:
            fuse = fuse.model_copy(update={"uuid": fuse_uuid})
        system.add_component(fuse)


def _load_matrix_impedance_reclosers_from_normalized(
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
            controller_id,
            in_service
        FROM matrix_impedance_reclosers
        ORDER BY id
        """
    ).fetchall()
    if not rows:
        return

    equipment_cache: dict[int, MatrixImpedanceRecloserEquipment] = {}
    controller_cache: dict[int, DistributionRecloserController] = {}
    controller_curve_cache: dict[int, TimeCurrentCurve] = {}
    controller_equipment_cache: dict[int, RecloserControllerEquipment] = {}

    for (
        recloser_id,
        name,
        from_bus_id,
        to_bus_id,
        substation_id,
        feeder_id,
        length,
        length_unit,
        equipment_id,
        controller_id,
        in_service,
    ) in rows:
        equipment = equipment_cache.get(equipment_id)
        if equipment is None:
            equipment_row = conn.execute(
                """
                SELECT name, construction, ampacity, ampacity_unit
                FROM matrix_impedance_recloser_equipment
                WHERE id = ?
                """,
                (equipment_id,),
            ).fetchone()
            if equipment_row is None:
                raise ValueError(
                    f"matrix_impedance_recloser_equipment_id={equipment_id} not found"
                )
            r_matrix, r_unit = _load_impedance_matrix(conn, equipment_id, "RECLOSER", "R")
            x_matrix, x_unit = _load_impedance_matrix(conn, equipment_id, "RECLOSER", "X")
            c_matrix, c_unit = _load_impedance_matrix(conn, equipment_id, "RECLOSER", "C")
            equipment = MatrixImpedanceRecloserEquipment(
                name=equipment_row[0],
                construction=LineType(equipment_row[1]),
                ampacity=Current(equipment_row[2], equipment_row[3]),
                r_matrix=ResistancePULength(r_matrix, r_unit),
                x_matrix=ReactancePULength(x_matrix, x_unit),
                c_matrix=CapacitancePULength(c_matrix, c_unit),
            )
            equipment_uuid = _fetch_component_uuid(
                conn,
                "matrix_impedance_recloser_equipment",
                equipment_id,
            )
            if equipment_uuid is not None:
                equipment = equipment.model_copy(update={"uuid": equipment_uuid})
            equipment_cache[equipment_id] = equipment

        controller = _load_distribution_recloser_controller(
            conn,
            controller_id,
            controller_cache,
            controller_curve_cache,
            controller_equipment_cache,
        )

        phases_rows = conn.execute(
            """
            SELECT phase
            FROM matrix_impedance_recloser_phases
            WHERE recloser_id = ?
            ORDER BY position_index
            """,
            (recloser_id,),
        ).fetchall()
        state_rows = conn.execute(
            """
            SELECT is_closed
            FROM recloser_phase_states
            WHERE recloser_id = ?
            ORDER BY position_index
            """,
            (recloser_id,),
        ).fetchall()
        recloser = MatrixImpedanceRecloser(
            name=name,
            buses=[buses_by_id[from_bus_id], buses_by_id[to_bus_id]],
            substation=substations_by_id[substation_id],
            feeder=feeders_by_id[feeder_id],
            length=Distance(length, length_unit),
            phases=[Phase(phase) for (phase,) in phases_rows],
            is_closed=[bool(state) for (state,) in state_rows],
            equipment=equipment,
            controller=controller,
            in_service=bool(in_service),
        )
        recloser_uuid = _fetch_component_uuid(conn, "matrix_impedance_reclosers", recloser_id)
        if recloser_uuid is not None:
            recloser = recloser.model_copy(update={"uuid": recloser_uuid})
        system.add_component(recloser)
