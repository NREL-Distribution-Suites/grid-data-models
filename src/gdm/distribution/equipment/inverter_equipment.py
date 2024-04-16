"""This module contains load equipment."""

from typing import Annotated, Optional

from infrasys import Component
from pydantic import Field

from gdm.quantities import PositiveApparentPower, ActivePowerPUTime
from gdm.distribution.curve import Curve
from gdm.constants import PINT_SCHEMA


class InverterEquipment(Component):
    """Interface for inverter equipment."""

    name: Annotated[str, Field("", description="Name of the inverter controller.")]
    capacity: Annotated[
        PositiveApparentPower,
        PINT_SCHEMA,
        Field(..., description="Apparent power rating for the inverter."),
    ]
    rise_limit: Annotated[
        Optional[ActivePowerPUTime],
        PINT_SCHEMA,
        Field(..., description="The rise in power output allowed per unit of time"),
    ]

    fall_limit: Annotated[
        Optional[ActivePowerPUTime],
        PINT_SCHEMA,
        Field(..., description="The fall in power output allowed per unit of time"),
    ]
    eff_curve: Annotated[Optional[Curve], Field(None, description="Efficency curve for inverter.")]

    @classmethod
    def example(cls) -> "InverterEquipment":
        """Example for load model."""
        return InverterEquipment(
            capacity=PositiveApparentPower(3.8, "kva"),
            rise_limit=ActivePowerPUTime(1.1, "kW/minute"),
            fall_limit=ActivePowerPUTime(1.1, "kW/minute"),
        )
