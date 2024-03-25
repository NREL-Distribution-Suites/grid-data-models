""" This module contains interface for distribution inverter controllers."""

from typing import Annotated, Optional

from infrasys.component_models import Component
from pydantic import Field

from gdm.quantities import (
    PositiveApparentPower,
    ActivePowerPUTime,
)
from gdm.distribution.curve import Curve


class InverterController(Component):
    """Interface for Inverter controllers."""

    inverter_capacity: Annotated[
        PositiveApparentPower, Field(..., description="Apparent power rating for the inverter.")
    ]

    rise_limit: Annotated[
        Optional[ActivePowerPUTime],
        Field(..., description="The rise in power output allowed per unit of time"),
    ]

    fall_limit: Annotated[
        Optional[ActivePowerPUTime],
        Field(..., description="The fall in power output allowed per unit of time"),
    ]

    @classmethod
    def example(cls) -> "PowerfactorInverterController":
        "Example of a Generic Inverter controller"
        return InverterController(
            inverter_capacity=PositiveApparentPower(3.8, "kva"),
            rise_limit=ActivePowerPUTime(1.1, "kW/minute"),
            fall_limit=ActivePowerPUTime(1.1, "kW/minute"),
        )


class PowerfactorInverterController(InverterController):
    """Interface for an Inverter Controller using powerfactor to determine power output."""

    power_factor: Annotated[
        float, Field(ge=-1, le=1, description="The power factor used for the controller.")
    ]

    @classmethod
    def example(cls) -> "PowerfactorInverterController":
        "Example of a Power Factor based Inverter controller"
        return PowerfactorInverterController(
            inverter_capacity=PositiveApparentPower(3.8, "kva"),
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
            inverter_capacity=PositiveApparentPower(3.8, "kva"),
            rise_limit=ActivePowerPUTime(1.1, "kW/minute"),
            fall_limit=ActivePowerPUTime(1.1, "kW/minute"),
            volt_var_curve=Curve.example(),
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
            inverter_capacity=PositiveApparentPower(3.8, "kva"),
            rise_limit=ActivePowerPUTime(1.1, "kW/minute"),
            fall_limit=ActivePowerPUTime(1.1, "kW/minute"),
            volt_var_vol_watt_curve=Curve.vv_vw_example(),
        )
