""" This module contains interface for distribution controllers."""
from typing import Annotated, Optional

from infrasys.component_models import Component
from infrasys.quantities import Time
from pydantic import Field

from gdm.distribution.distribution_enum import ControllerType
from gdm.quantities import (
    PositiveVoltage,
)
class RegulatorController(Component):
    """Interface for a Regulator Controller."""
    delay: Annotated[
            Optional[Time], Field(..., description="Delay for the first tap change operation")
    ]
    controller_type: Annotated[
        ControllerType,
        Field(..., description="Whether the controller uses a PT (Potenial Transformer) or a CT (Current Transformer).")
    ]
    controller_ratio: Annotated[
            float, Field(..., ge=0, description="The voltage (potential) or current transformer ratio used to step down the voltage for the controller")
    ]

    bandwidth: Annotated[
        PositiveVoltage, Field(..., description="The voltage bandwidth on the controller before a change occurs in the regulator")
    ]

    bandcenter: Annotated[
        PositiveVoltage, Field(..., description="The voltage bandcenter on the controller.")
    ]

    #TODO: Should this be done in Voltage like maximum_tap?
    highstep: Annotated[
        int, Field(ge=0, description="Maximum number of steps upwards that can be made. ie the highest step position from neutral.")
    ]

    #TODO: Should this be done in Voltage like minimum_tap?
    lowstep: Annotated[
        int, Field(ge=0, description="Maximum number of steps downwards that can be made. ie the lowest step position from neutral.")
    ]

    @classmethod
    def example(cls) -> "RegulatorController":
        """Example for a Regulator Controller."""
        return RegulatorController(
            delay = Time(10, "seconds"),
            controller_type = "PT",
            controller_ratio = 60,
            bandwidth = PositiveVoltage(3, "volts"),
            bandcenter = PositiveVoltage(120, "volts"),
            highstep = 16,
            lowstep = 16,
        )

