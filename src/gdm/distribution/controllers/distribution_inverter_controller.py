""" This module contains interface for distribution inverter controllers."""

from typing import Annotated

from pydantic import Field

from gdm.distribution.curve import Curve
from gdm.distribution.controllers.base.inverter_controller_base import InverterControllerBase


class PowerfactorInverterController(InverterControllerBase):
    """Interface for an Inverter Controller using powerfactor to determine power output."""

    power_factor: Annotated[
        float, Field(ge=-1, le=1, description="The power factor used for the controller.")
    ]

    @classmethod
    def example(cls) -> "PowerfactorInverterController":
        "Example of a Power Factor based Inverter controller"
        return PowerfactorInverterController(
            power_factor=0.95,
        )


class VoltVarInverterController(InverterControllerBase):
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

    @classmethod
    def example(cls) -> "VoltVarInverterController":
        "Example of a Volt-Var Inverter Controller"
        return VoltVarInverterController(
            volt_var_curve=Curve.example(),
            var_follow=False,
        )


class VoltWattInverterController(InverterControllerBase):
    """Interface for a Volt-Var Inverter Controller."""

    volt_watt_curve: Annotated[
        Curve, Field(..., description="The volt-watt curve that is being applied.")
    ]

    @classmethod
    def example(cls) -> "VoltWattInverterController":
        "Example of a Volt-Watt Inverter Controller"
        return VoltWattInverterController(
            volt_watt_curve=Curve(curve_x=[0.5, 1.06, 1.1, 1.5], curve_y=[1.0, 1.0, 0.0, 0.0]),
        )


class VoltVarVoltWattInverterController(VoltVarInverterController):
    """Interface for a Volt-Var Volt-Watt Inverter Controller."""

    volt_watt_curve: Annotated[
        Curve, Field(..., description="The volt-watt curve that is being applied.")
    ]
    var_priority: Annotated[
        bool,
        Field(
            ...,
            description="""True means var priority and false means watt priority.""",
        ),
    ]

    @classmethod
    def example(cls) -> "VoltVarVoltWattInverterController":
        "Example of a Volt-Var Volt-Watt Inverter Controller"
        return VoltVarVoltWattInverterController(
            volt_var_curve=Curve.example(),
            volt_watt_curve=Curve(curve_x=[0.5, 1.06, 1.1, 1.5], curve_y=[1.0, 1.0, 0.0, 0.0]),
            var_priority=True,
            var_follow=False,
        )
