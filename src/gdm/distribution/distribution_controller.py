""" This module contains interface for distribution controllers."""
from typing import Annotated, Optional

from infrasys.component_models import Component
from infrasys.quantities import Time
from pydantic import Field

from gdm.distribution.distribution_enum import OnOffSetting, Phase, ControllerType
from gdm.quantities import (
    PositiveActivePower,
    PositiveReactivePower,
    PositiveVoltage,
    PositiveCurrent,
)
class Curve(Component):
    """An interface for represening volt-var or volt-watt curves."""

    curve_x: Annotated[
        list[float], Field(..., description="The x values of the curve")
    ]

    curve_y: Annotated[
        list[float], Field(..., description="The y values of the curve")
    ]

    @classmethod
    def example(cls) -> "Curve":
        """Example of a Curve (Volt-Var IEEE-1547 standard)."""
        return Curve(
            curve_x = [0.5,0.92,0.98,1.02,1.08,1.5],
            curve_y = [1.0,1.0,0.0,0.0,-1.0,-1.0]
        )

class SolarController(Component):
    """Interface for Solar PV controllers."""

    active_rating: Annotated[
        PositiveActivePower, Field(..., description="Active power rating for the PV controller.")
    ]

    reactive_rating: Annotated[
        PositiveReactivePower, Field(..., description="Reactive power rating for the PV controller.")
    ]

    # TODO: Note that if this is not applicable, then it's set to 0
    cutout_percent: Annotated[
        float, Field(ge=0,le=100, description="If the per-unit power drops below this value the PV output is turned off.")
    ]

    # TODO: Note that if this is not applicable, then it's set to 0
    cutin_percent: Annotated[
        float, Field(ge=0,le=100, description="If the per-unit power rises above this value the PV output is turned on.")
    ]


    # TODO: Should specificity be provided in units e.g kw/min as a unit?
    rise_limit: Annotated[
        Optional[float],
        Field(ge=0,le=100, description="The percentage rise in power output allowed per minute")
    ]

    fall_limit: Annotated[
        Optional[float],
        Field(ge=0,le=100, description="The percentage fall in power output allowed per minute")
    ]


class PowerfactorSolarController(SolarController):
    """Interface for a PV Controller using powerfactor to determine power output."""

    power_factor: Annotated[
        float, Field(..., description="The power factor used for the controller.")
    ]

class FixedValueSolarController(SolarController):
    """Interface for a PV Controller with set value outputs."""

    real_power: Annotated[
        PositiveActivePower, Field(..., description="The active power attempted to be injected by the controller.")
    ]

    reactive_power: Annotated[
        PositiveReactivePower, Field(..., description="The reactive power attempted to be injected by the controller.")
    ]

class VoltVarSolarController(SolarController):
    """Interface for a Volt-Var PV Controller."""

    volt_var_curve: Annotated[
        Curve, Field(..., description="The volt-var curve that is being applied.")
    ]

    @classmethod
    def example(cls) -> "VoltVarSolarController":
        "Example of a Volt-Var Solar Controller"
        return VoltVarSolarController(
                active_rating = PositiveActivePower(3.8, "kW"),
                reactive_rating = PositiveReactivePower(3.8, "kvar"),
                cutin_percent = 10,
                cutout_percent = 10,
                rise_limit=100,
                fall_limit=100,
                volt_var_curve = Curve.example()
        )


class VoltWattSolarController(SolarController):
    """Interface for a Volt-Watt PV Controller."""

    volt_watt_curve: Annotated[
        Curve, Field(..., description="The volt-watt curve that is being applied.")
    ]


class CapacitorController(Component):
    """Interface for capacitor controllers."""

    on_off: Annotated[
            OnOffSetting, Field(..., description="Whether the range of the control mode turns the capacitor on or off.")
    ]

    monitored_phases: Annotated[
            list[Phase], Field(..., description="The phase that the controller is connected to")
    ]

    controller_type: Annotated[
        ControllerType,
        Field(..., description="Whether the controller uses a PT (Potenial Transformer) or a CT (Current Transformer).")
    ]
    controller_ratio: Annotated[
            float, Field(..., ge=0, description="The voltage (potential) or current transformer ratio used to step down the voltage for the controller")
    ]

class VoltageCapacitorController(CapacitorController):
    """Interface for a Capacitor Controller which uses voltage."""
    low_voltage: Annotated[
            PositiveVoltage, Field(..., description="Low value of the voltage being controlled by the capacitor controller.")
    ]

    high_voltage: Annotated[
            PositiveVoltage, Field(..., description="High value of the voltage being controlled by the capacitor controller.")
    ]
    @classmethod
    def example(cls) -> "VoltageCapacitorController":
        """Example for a VoltageCapacitorController."""
        return VoltageCapacitorController(
                on_off="ON",
                monitored_phases=[Phase.A],
                controller_type= "PT",
                controller_ratio=60,
                low_voltage = PositiveVoltage(120, "volt"),
                high_voltage = PositiveVoltage(125, "volt"),
        )



class ActivePowerCapacitorController(CapacitorController):
    """Interface for a Capacitor Controller which uses active power."""
    low_power: Annotated[
            PositiveActivePower, Field(..., description="Low value of the active power being controlled by the capacitor controller.")
    ]

    high_power: Annotated[
            PositiveActivePower, Field(..., description="High value of the active power being controlled by the capacitor controller.")
    ]

class ReactivePowerCapacitorController(CapacitorController):
    """Interface for a Capacitor Controller which uses reactive power."""
    low_power: Annotated[
            PositiveReactivePower, Field(..., description="Low value of the reactive power being controlled by the capacitor controller.")
    ]

    high_power: Annotated[
            PositiveReactivePower, Field(..., description="High value of the reactive power being controlled by the capacitor controller.")
    ]

class CurrentCapacitorController(CapacitorController):
    """Interface for a Capacitor Controller which uses current."""
    low_current: Annotated[
            PositiveCurrent, Field(..., description="Low value of the current being controlled by the capacitor controller.")
    ]

    high_current: Annotated[
            PositiveCurrent, Field(..., description="High value of the current being controlled by the capacitor controller.")
    ]

class TimedCapacitorController(CapacitorController):
    """Interface for a Capacitor Controller which uses a timed controller."""
    start_time: Annotated[
            Time, Field(..., description="Start time for the capacitor controller.")
    ]

    end_time: Annotated[
            Time, Field(..., description="End time for the capacitor controller.")
    ]
