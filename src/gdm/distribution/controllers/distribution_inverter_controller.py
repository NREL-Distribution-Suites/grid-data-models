""" This module contains interface for distribution inverter controllers."""

from typing import Annotated, Literal

from infrasys import Component
from pydantic import Field

from gdm.distribution.curve import Curve
from gdm.distribution.controllers.base.inverter_controller_base import (
    ReactivePowerInverterControllerBase,
    ActivePowerInverterControllerBase,
)
from gdm.distribution.distribution_enum import ControllerSupport


class PowerfactorInverterController(ReactivePowerInverterControllerBase):
    """Interface for an Inverter Controller using powerfactor to determine power output."""

    power_factor: Annotated[
        float, Field(ge=-1, le=1, description="The power factor used for the controller.")
    ]
    supported_by : Literal[ControllerSupport.BATTERY_AND_SOLAR] = ControllerSupport.BATTERY_AND_SOLAR

    @classmethod
    def example(cls) -> "PowerfactorInverterController":
        "Example of a Power Factor based Inverter controller"
        return PowerfactorInverterController(
            power_factor=0.95,
        )


class VoltVarInverterController(ReactivePowerInverterControllerBase):
    """Interface for a Volt-Var Inverter Controller."""

    volt_var_curve: Annotated[
        Curve, Field(..., description="The volt-var curve that is being applied.")
    ]
    var_follow: Annotated[
        bool,
        Field(
            ...,
            description="""Set to false if you want inverter reactive power
                        generation absorption to respect inverter status""",
        ),
    ]
    supported_by: Literal[ControllerSupport.BATTERY_AND_SOLAR] = ControllerSupport.BATTERY_AND_SOLAR

    @classmethod
    def example(cls) -> "VoltVarInverterController":
        "Example of a Volt-Var Inverter Controller"
        return VoltVarInverterController(
            volt_var_curve=Curve.example(),
            var_follow=False,
        )


class VoltWattInverterController(ActivePowerInverterControllerBase):
    """Interface for a Volt-Var Inverter Controller."""

    volt_watt_curve: Annotated[
        Curve, Field(..., description="The volt-watt curve that is being applied.")
    ]
    supported_by: Literal[ControllerSupport.SOLAR_ONLY] = ControllerSupport.SOLAR_ONLY

    @classmethod
    def example(cls) -> "VoltWattInverterController":
        "Example of a Volt-Watt Inverter Controller"
        return VoltWattInverterController(
            volt_watt_curve=Curve(curve_x=[0.5, 1.06, 1.1, 1.5], curve_y=[1.0, 1.0, 0.0, 0.0]),
        )


class InverterController(Component):
    """Interface for Inverter controllers that control active and reactive power."""

    name: Annotated[str, Field("", description="Name of the inverter controller.")]
    
    active_power_control: Annotated[
        ActivePowerInverterControllerBase | None,
        Field(None, description="Controller settings to control active power output of the inverter",),
    ]
    
    reactive_power_control: Annotated[
        ReactivePowerInverterControllerBase | None,
        Field(None, description="Controller settings to control reactive power output of the inverter",),
    ]

    prioritize_active_power: Annotated[
        bool, Field(..., description="If True, the controller tries to prioritize active power.")
    ]

    night_mode: Annotated[
        bool, Field(..., description="If True, the controller controls reactive power even when there is no active power.")
    ]

    @classmethod
    def example(cls) -> "InverterController":
        "Example of a Volt-Watt Inverter Controller"
        return InverterController(
            name="inv1",
            active_power_control=VoltWattInverterController.example(),
            reactive_power_control=PowerfactorInverterController.example(),
            prioritize_active_power=False,        
            night_mode=True,
        )
    