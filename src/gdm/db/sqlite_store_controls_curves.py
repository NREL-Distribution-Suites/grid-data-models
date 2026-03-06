"""Shared inverter control and curve helpers for SQLite GDM persistence."""

from __future__ import annotations

import sqlite3
from datetime import time
from uuid import UUID

from infrasys.quantities import Time

from gdm.db.sqlite_store_identity import _fetch_component_uuid, _upsert_component_uuid_map
from gdm.distribution.common.curve import Curve, TimeCurrentCurve
from gdm.distribution.controllers.distribution_inverter_controller import (
    CapacityFirmingControlSetting,
    DemandChargeControlSetting,
    InverterController,
    PeakShavingBaseLoadingControlSetting,
    PowerfactorControlSetting,
    SelfConsumptionControlSetting,
    TimeBasedControlSetting,
    TimeOfUseControlSetting,
    VoltVarControlSetting,
    VoltWattControlSetting,
)
from gdm.quantities import ActivePower, ActivePowerOverTime, Current


def _upsert_curve(
    conn: sqlite3.Connection, curve: Curve, curve_id_by_uuid: dict[UUID, int]
) -> int:
    curve_id = curve_id_by_uuid.get(curve.uuid)
    if curve_id is not None:
        return curve_id

    cursor = conn.execute(
        "INSERT INTO curves(name) VALUES(?)",
        (curve.name,),
    )
    curve_id = int(cursor.lastrowid)
    _upsert_component_uuid_map(conn, "curves", curve_id, curve.uuid)
    for position_index, (x_value, y_value) in enumerate(zip(curve.curve_x, curve.curve_y)):
        conn.execute(
            "INSERT INTO curve_points(curve_id, position_index, x_value, y_value) VALUES(?, ?, ?, ?)",
            (curve_id, position_index, float(x_value), float(y_value)),
        )

    curve_id_by_uuid[curve.uuid] = curve_id
    return curve_id


def _upsert_inverter_controller(
    conn: sqlite3.Connection,
    controller: InverterController | None,
    curve_id_by_uuid: dict[UUID, int],
    active_control_id_by_uuid: dict[UUID, int],
    reactive_control_id_by_uuid: dict[UUID, int],
    controller_id_by_uuid: dict[UUID, int],
) -> int | None:
    if controller is None:
        return None

    existing = controller_id_by_uuid.get(controller.uuid)
    if existing is not None:
        return existing

    active_control_id = _upsert_inverter_active_control(
        conn,
        controller.active_power_control,
        curve_id_by_uuid,
        active_control_id_by_uuid,
    )
    reactive_control_id = _upsert_inverter_reactive_control(
        conn,
        controller.reactive_power_control,
        curve_id_by_uuid,
        reactive_control_id_by_uuid,
    )

    cursor = conn.execute(
        """
        INSERT INTO inverter_controllers(
            name,
            prioritize_active_power,
            night_mode,
            active_power_control_id,
            reactive_power_control_id
        ) VALUES(?, ?, ?, ?, ?)
        """,
        (
            controller.name,
            1 if controller.prioritize_active_power else 0,
            1 if controller.night_mode else 0,
            active_control_id,
            reactive_control_id,
        ),
    )
    controller_id = int(cursor.lastrowid)
    _upsert_component_uuid_map(conn, "inverter_controllers", controller_id, controller.uuid)
    controller_id_by_uuid[controller.uuid] = controller_id
    return controller_id


def _upsert_inverter_active_control(
    conn: sqlite3.Connection,
    active_control,
    curve_id_by_uuid: dict[UUID, int],
    active_control_id_by_uuid: dict[UUID, int],
) -> int | None:
    if active_control is None:
        return None

    existing = active_control_id_by_uuid.get(active_control.uuid)
    if existing is not None:
        return existing

    values = {
        "name": active_control.name,
        "controller_type": None,
        "supported_by": active_control.supported_by.value,
        "volt_watt_curve_id": None,
        "peak_shaving_target": None,
        "peak_shaving_target_unit": None,
        "base_loading_target": None,
        "base_loading_target_unit": None,
        "max_active_power_roc": None,
        "max_active_power_roc_unit": None,
        "min_active_power_roc": None,
        "min_active_power_roc_unit": None,
        "charging_start_time": None,
        "charging_end_time": None,
        "discharging_start_time": None,
        "discharging_end_time": None,
        "charging_power": None,
        "charging_power_unit": None,
        "discharging_power": None,
        "discharging_power_unit": None,
        "tariff_id": None,
    }

    if isinstance(active_control, VoltWattControlSetting):
        values["controller_type"] = "VOLT_WATT"
        values["volt_watt_curve_id"] = _upsert_curve(
            conn, active_control.volt_watt_curve, curve_id_by_uuid
        )
    elif isinstance(active_control, PeakShavingBaseLoadingControlSetting):
        values["controller_type"] = "PEAK_SHAVING"
        values["peak_shaving_target"] = float(active_control.peak_shaving_target.magnitude)
        values["peak_shaving_target_unit"] = str(active_control.peak_shaving_target.units)
        values["base_loading_target"] = float(active_control.base_loading_target.magnitude)
        values["base_loading_target_unit"] = str(active_control.base_loading_target.units)
    elif isinstance(active_control, CapacityFirmingControlSetting):
        values["controller_type"] = "CAPACITY_FIRMING"
        values["max_active_power_roc"] = float(active_control.max_active_power_roc.magnitude)
        values["max_active_power_roc_unit"] = str(active_control.max_active_power_roc.units)
        values["min_active_power_roc"] = float(active_control.min_active_power_roc.magnitude)
        values["min_active_power_roc_unit"] = str(active_control.min_active_power_roc.units)
    elif isinstance(active_control, TimeBasedControlSetting):
        values["controller_type"] = "TIME_BASED"
        values["charging_start_time"] = active_control.charging_start_time.strftime("%H:%M:%S")
        values["charging_end_time"] = active_control.charging_end_time.strftime("%H:%M:%S")
        values["discharging_start_time"] = active_control.discharging_start_time.strftime(
            "%H:%M:%S"
        )
        values["discharging_end_time"] = active_control.discharging_end_time.strftime("%H:%M:%S")
        values["charging_power"] = float(active_control.charging_power.magnitude)
        values["charging_power_unit"] = str(active_control.charging_power.units)
        values["discharging_power"] = float(active_control.discharging_power.magnitude)
        values["discharging_power_unit"] = str(active_control.discharging_power.units)
    elif isinstance(active_control, SelfConsumptionControlSetting):
        values["controller_type"] = "SELF_CONSUMPTION"
    elif isinstance(active_control, TimeOfUseControlSetting):
        values["controller_type"] = "TIME_OF_USE"
    elif isinstance(active_control, DemandChargeControlSetting):
        values["controller_type"] = "DEMAND_CHARGE"
    else:
        return None

    cursor = conn.execute(
        """
        INSERT INTO inverter_active_power_controls(
            name,
            controller_type,
            supported_by,
            volt_watt_curve_id,
            peak_shaving_target,
            peak_shaving_target_unit,
            base_loading_target,
            base_loading_target_unit,
            max_active_power_roc,
            max_active_power_roc_unit,
            min_active_power_roc,
            min_active_power_roc_unit,
            charging_start_time,
            charging_end_time,
            discharging_start_time,
            discharging_end_time,
            charging_power,
            charging_power_unit,
            discharging_power,
            discharging_power_unit,
            tariff_id
        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            values["name"],
            values["controller_type"],
            values["supported_by"],
            values["volt_watt_curve_id"],
            values["peak_shaving_target"],
            values["peak_shaving_target_unit"],
            values["base_loading_target"],
            values["base_loading_target_unit"],
            values["max_active_power_roc"],
            values["max_active_power_roc_unit"],
            values["min_active_power_roc"],
            values["min_active_power_roc_unit"],
            values["charging_start_time"],
            values["charging_end_time"],
            values["discharging_start_time"],
            values["discharging_end_time"],
            values["charging_power"],
            values["charging_power_unit"],
            values["discharging_power"],
            values["discharging_power_unit"],
            values["tariff_id"],
        ),
    )
    active_control_id = int(cursor.lastrowid)
    _upsert_component_uuid_map(
        conn,
        "inverter_active_power_controls",
        active_control_id,
        active_control.uuid,
    )
    active_control_id_by_uuid[active_control.uuid] = active_control_id
    return active_control_id


def _upsert_inverter_reactive_control(
    conn: sqlite3.Connection,
    reactive_control,
    curve_id_by_uuid: dict[UUID, int],
    reactive_control_id_by_uuid: dict[UUID, int],
) -> int | None:
    if reactive_control is None:
        return None

    existing = reactive_control_id_by_uuid.get(reactive_control.uuid)
    if existing is not None:
        return existing

    values = {
        "name": reactive_control.name,
        "controller_type": None,
        "supported_by": reactive_control.supported_by.value,
        "power_factor": None,
        "volt_var_curve_id": None,
        "var_follow": None,
    }

    if isinstance(reactive_control, PowerfactorControlSetting):
        values["controller_type"] = "POWER_FACTOR"
        values["power_factor"] = reactive_control.power_factor
    elif isinstance(reactive_control, VoltVarControlSetting):
        values["controller_type"] = "VOLT_VAR"
        values["volt_var_curve_id"] = _upsert_curve(
            conn, reactive_control.volt_var_curve, curve_id_by_uuid
        )
        values["var_follow"] = 1 if reactive_control.var_follow else 0
    else:
        return None

    cursor = conn.execute(
        """
        INSERT INTO inverter_reactive_power_controls(
            name,
            controller_type,
            supported_by,
            power_factor,
            volt_var_curve_id,
            var_follow
        ) VALUES(?, ?, ?, ?, ?, ?)
        """,
        (
            values["name"],
            values["controller_type"],
            values["supported_by"],
            values["power_factor"],
            values["volt_var_curve_id"],
            values["var_follow"],
        ),
    )
    reactive_control_id = int(cursor.lastrowid)
    _upsert_component_uuid_map(
        conn,
        "inverter_reactive_power_controls",
        reactive_control_id,
        reactive_control.uuid,
    )
    reactive_control_id_by_uuid[reactive_control.uuid] = reactive_control_id
    return reactive_control_id


def _load_curve(conn: sqlite3.Connection, curve_id: int, curve_cache: dict[int, Curve]) -> Curve:
    curve = curve_cache.get(curve_id)
    if curve is not None:
        return curve

    row = conn.execute("SELECT name FROM curves WHERE id = ?", (curve_id,)).fetchone()
    if row is None:
        raise ValueError(f"curve_id={curve_id} not found")
    (curve_name,) = row

    points = conn.execute(
        "SELECT x_value, y_value FROM curve_points WHERE curve_id = ? ORDER BY position_index",
        (curve_id,),
    ).fetchall()
    curve = Curve(name=curve_name, curve_x=[x for x, _ in points], curve_y=[y for _, y in points])
    curve_uuid = _fetch_component_uuid(conn, "curves", curve_id)
    if curve_uuid is not None:
        curve = curve.model_copy(update={"uuid": curve_uuid})
    curve_cache[curve_id] = curve
    return curve


def _load_inverter_active_control(
    conn: sqlite3.Connection,
    control_id: int,
    curve_cache: dict[int, Curve],
    active_control_cache: dict[int, object],
):
    existing = active_control_cache.get(control_id)
    if existing is not None:
        return existing

    row = conn.execute(
        """
        SELECT
            name,
            controller_type,
            supported_by,
            volt_watt_curve_id,
            peak_shaving_target,
            peak_shaving_target_unit,
            base_loading_target,
            base_loading_target_unit,
            max_active_power_roc,
            max_active_power_roc_unit,
            min_active_power_roc,
            min_active_power_roc_unit,
            charging_start_time,
            charging_end_time,
            discharging_start_time,
            discharging_end_time,
            charging_power,
            charging_power_unit,
            discharging_power,
            discharging_power_unit
        FROM inverter_active_power_controls
        WHERE id = ?
        """,
        (control_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"inverter_active_power_control_id={control_id} not found")

    (
        name,
        controller_type,
        _,
        volt_watt_curve_id,
        peak_shaving_target,
        peak_shaving_target_unit,
        base_loading_target,
        base_loading_target_unit,
        max_active_power_roc,
        max_active_power_roc_unit,
        min_active_power_roc,
        min_active_power_roc_unit,
        charging_start_time,
        charging_end_time,
        discharging_start_time,
        discharging_end_time,
        charging_power,
        charging_power_unit,
        discharging_power,
        discharging_power_unit,
    ) = row

    control = None
    if controller_type == "VOLT_WATT" and volt_watt_curve_id is not None:
        control = VoltWattControlSetting(
            name=name,
            volt_watt_curve=_load_curve(conn, volt_watt_curve_id, curve_cache),
        )
    elif controller_type == "PEAK_SHAVING":
        control = PeakShavingBaseLoadingControlSetting(
            name=name,
            peak_shaving_target=ActivePower(peak_shaving_target, peak_shaving_target_unit),
            base_loading_target=ActivePower(base_loading_target, base_loading_target_unit),
        )
    elif controller_type == "CAPACITY_FIRMING":
        control = CapacityFirmingControlSetting(
            name=name,
            max_active_power_roc=ActivePowerOverTime(
                max_active_power_roc, max_active_power_roc_unit
            ),
            min_active_power_roc=ActivePowerOverTime(
                min_active_power_roc, min_active_power_roc_unit
            ),
        )
    elif controller_type == "TIME_BASED":
        control = TimeBasedControlSetting(
            name=name,
            charging_start_time=time.fromisoformat(charging_start_time),
            charging_end_time=time.fromisoformat(charging_end_time),
            discharging_start_time=time.fromisoformat(discharging_start_time),
            discharging_end_time=time.fromisoformat(discharging_end_time),
            charging_power=ActivePower(charging_power, charging_power_unit),
            discharging_power=ActivePower(discharging_power, discharging_power_unit),
        )
    elif controller_type == "SELF_CONSUMPTION":
        control = SelfConsumptionControlSetting(name=name)

    if control is not None:
        control_uuid = _fetch_component_uuid(conn, "inverter_active_power_controls", control_id)
        if control_uuid is not None:
            control = control.model_copy(update={"uuid": control_uuid})
        active_control_cache[control_id] = control

    return control


def _load_inverter_reactive_control(
    conn: sqlite3.Connection,
    control_id: int,
    curve_cache: dict[int, Curve],
    reactive_control_cache: dict[int, object],
):
    existing = reactive_control_cache.get(control_id)
    if existing is not None:
        return existing

    row = conn.execute(
        """
        SELECT
            name,
            controller_type,
            supported_by,
            power_factor,
            volt_var_curve_id,
            var_follow
        FROM inverter_reactive_power_controls
        WHERE id = ?
        """,
        (control_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"inverter_reactive_power_control_id={control_id} not found")

    name, controller_type, _, power_factor, volt_var_curve_id, var_follow = row

    control = None
    if controller_type == "POWER_FACTOR":
        control = PowerfactorControlSetting(name=name, power_factor=power_factor)
    elif controller_type == "VOLT_VAR" and volt_var_curve_id is not None:
        control = VoltVarControlSetting(
            name=name,
            volt_var_curve=_load_curve(conn, volt_var_curve_id, curve_cache),
            var_follow=bool(var_follow),
        )

    if control is not None:
        control_uuid = _fetch_component_uuid(conn, "inverter_reactive_power_controls", control_id)
        if control_uuid is not None:
            control = control.model_copy(update={"uuid": control_uuid})
        reactive_control_cache[control_id] = control

    return control


def _load_inverter_controller(
    conn: sqlite3.Connection,
    controller_id: int,
    curve_cache: dict[int, Curve],
    active_control_cache: dict[int, object],
    reactive_control_cache: dict[int, object],
    controller_cache: dict[int, InverterController],
) -> InverterController | None:
    existing = controller_cache.get(controller_id)
    if existing is not None:
        return existing

    row = conn.execute(
        """
        SELECT
            name,
            prioritize_active_power,
            night_mode,
            active_power_control_id,
            reactive_power_control_id
        FROM inverter_controllers
        WHERE id = ?
        """,
        (controller_id,),
    ).fetchone()
    if row is None:
        return None

    (
        name,
        prioritize_active_power,
        night_mode,
        active_power_control_id,
        reactive_power_control_id,
    ) = row

    active_control = None
    reactive_control = None
    if active_power_control_id is not None:
        active_control = _load_inverter_active_control(
            conn,
            active_power_control_id,
            curve_cache,
            active_control_cache,
        )
    if reactive_power_control_id is not None:
        reactive_control = _load_inverter_reactive_control(
            conn,
            reactive_power_control_id,
            curve_cache,
            reactive_control_cache,
        )

    controller = InverterController(
        name=name,
        prioritize_active_power=bool(prioritize_active_power),
        night_mode=bool(night_mode),
        active_power_control=active_control,
        reactive_power_control=reactive_control,
    )
    controller_uuid = _fetch_component_uuid(conn, "inverter_controllers", controller_id)
    if controller_uuid is not None:
        controller = controller.model_copy(update={"uuid": controller_uuid})
    controller_cache[controller_id] = controller
    return controller


def _upsert_time_current_curve(
    conn: sqlite3.Connection,
    curve: TimeCurrentCurve,
    curve_id_by_uuid: dict[UUID, int],
) -> int:
    existing = curve_id_by_uuid.get(curve.uuid)
    if existing is not None:
        return existing

    cursor = conn.execute(
        "INSERT INTO time_current_curves(name) VALUES(?)",
        (curve.name,),
    )
    curve_id = int(cursor.lastrowid)
    _upsert_component_uuid_map(conn, "time_current_curves", curve_id, curve.uuid)

    for position_index, (current_value, time_value) in enumerate(
        zip(curve.curve_x.magnitude, curve.curve_y.magnitude)
    ):
        conn.execute(
            """
            INSERT INTO time_current_curve_points(
                curve_id,
                position_index,
                current_value,
                current_unit,
                time_value,
                time_unit
            ) VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                curve_id,
                position_index,
                float(current_value),
                str(curve.curve_x.units),
                float(time_value),
                str(curve.curve_y.units),
            ),
        )

    curve_id_by_uuid[curve.uuid] = curve_id
    return curve_id


def _load_time_current_curve(
    conn: sqlite3.Connection,
    curve_id: int,
    curve_cache: dict[int, TimeCurrentCurve],
) -> TimeCurrentCurve:
    cached = curve_cache.get(curve_id)
    if cached is not None:
        return cached

    row = conn.execute(
        "SELECT name FROM time_current_curves WHERE id = ?",
        (curve_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"time_current_curve_id={curve_id} not found")

    points = conn.execute(
        """
        SELECT current_value, current_unit, time_value, time_unit
        FROM time_current_curve_points
        WHERE curve_id = ?
        ORDER BY position_index
        """,
        (curve_id,),
    ).fetchall()
    if not points:
        raise ValueError(f"time_current_curve_id={curve_id} has no points")

    current_unit = points[0][1]
    time_unit = points[0][3]
    curve = TimeCurrentCurve(
        name=row[0],
        curve_x=Current([current for current, _, _, _ in points], current_unit),
        curve_y=Time([time_value for _, _, time_value, _ in points], time_unit),
    )
    curve_uuid = _fetch_component_uuid(conn, "time_current_curves", curve_id)
    if curve_uuid is not None:
        curve = curve.model_copy(update={"uuid": curve_uuid})
    curve_cache[curve_id] = curve
    return curve
