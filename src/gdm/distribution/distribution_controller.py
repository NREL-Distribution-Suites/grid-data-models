from typing import Annotated

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
