""" This module contains interface for distribution inverter controllers."""
from typing import Annotated, Optional

from infrasys.component_models import Component
from pydantic import model_validator, Field

from gdm.quantities import (
    PositiveApparentPower,
    ActivePowerPUTime,
)
class Curve(Component):
    """An interface for representing a curve using x and y points. e.g for volt-var and volt-watt curves."""

    curve_x: Annotated[
        list[float], Field(..., description="The x values of the curve")
    ]

    curve_y: Annotated[
        list[float], Field(..., description="The y values of the curve")
    ]

    @model_validator(mode="after")
    def validate_fields(self) -> "Curve":
        if len(self.curve_x) != len(self.curve_y):
            msg = f"curve_x ({self.curve_x=}) and curve_y ({self.curve_y=}) have different lengths"
            raise ValueError(msg)
        return self

    @classmethod
    def example(cls) -> "Curve":
        """Example of a Curve (Volt-Var IEEE-1547 standard)."""
        return Curve(
            curve_x = [0.5,0.92,0.98,1.02,1.08,1.5],
            curve_y = [1.0,1.0,0.0,0.0,-1.0,-1.0]
        )

    @classmethod
    def vv_vw_example(cls) -> "Curve":
        """Example of a Curve (Volt-Var Volt-Watt IEEE-1547 standard)."""
        return Curve(
            curve_x = [0.5,1.06,1.1,1.5],
            curve_y = [1.0,1.0,0.0,0.0]
        )


class InverterController(Component):
    """Interface for Inverter controllers."""

    inverter_capacity: Annotated[
        PositiveApparentPower, Field(..., description="Apparent power rating for the inverter.")
    ]

    rise_limit: Annotated[
        Optional[ActivePowerPUTime],
        Field(..., description="The rise in power output allowed per unit of time")
    ]

    fall_limit: Annotated[
        Optional[ActivePowerPUTime],
        Field(..., description="The fall in power output allowed per unit of time")
    ]

    @classmethod
    def example(cls) -> "PowerfactorInverterController":
        "Example of a Generic Inverter controller"
        return InverterController(
                inverter_capacity = PositiveApparentPower(3.8, "kva"),
                rise_limit=ActivePowerPUTime(1.1, "kW/minute"),
                fall_limit=ActivePowerPUTime(1.1, "kW/minute"),
        )


class PowerfactorInverterController(InverterController):
    """Interface for an Inverter Controller using powerfactor to determine power output."""

    power_factor: Annotated[
        float, Field(ge=-1,le=1, description="The power factor used for the controller.")
    ]

    @classmethod
    def example(cls) -> "PowerfactorInverterController":
        "Example of a Power Factor based Inverter controller"
        return PowerfactorInverterController(
                inverter_capacity = PositiveApparentPower(3.8, "kva"),
                rise_limit=ActivePowerPUTime(1.1, "kW/minute"),
                fall_limit=ActivePowerPUTime(1.1, "kW/minute"),
                power_factor=0.95,
        )

class VoltVarInverterController(InverterController):
    """Interface for a Volt-Var Inverter Controller."""

    volt_var_curve: Annotated[
        Curve, Field(..., description="The volt-var curve that is being applied.")
    ]

    @classmethod
    def example(cls) -> "VoltVarInverterController":
        "Example of a Volt-Var Inverter Controller"
        return VoltVarInverterController(
                inverter_capacity = PositiveApparentPower(3.8, "kva"),
                rise_limit=ActivePowerPUTime(1.1, "kW/minute"),
                fall_limit=ActivePowerPUTime(1.1, "kW/minute"),
                volt_var_curve = Curve.example(),
        )


class VoltVarVoltWattInverterController(InverterController):
    """Interface for a Volt-Var Volt-Watt Inverter Controller."""

    volt_var_vol_watt_curve: Annotated[
        Curve, Field(..., description="The volt-var volt-watt curve that is being applied.")
    ]
    @classmethod
    def example(cls) -> "VoltVarVoltWattInverterController":
        "Example of a Volt-Var Volt-Watt Inverter Controller"
        return VoltVarVoltWattInverterController(
                inverter_capacity = PositiveApparentPower(3.8, "kva"),
                rise_limit=ActivePowerPUTime(1.1, "kW/minute"),
                fall_limit=ActivePowerPUTime(1.1, "kW/minute"),
                volt_var_vol_watt_curve = Curve.vv_vw_example()
        )




