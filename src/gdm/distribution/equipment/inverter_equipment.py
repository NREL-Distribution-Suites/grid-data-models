"""This module contains load equipment."""

from typing import Annotated, Optional

from infrasys import Component
from pydantic import Field

from gdm.quantities import PositiveApparentPower, ActivePowerPUTime


class InverterEquipment(Component):
    """Interface for inverter equipment."""

    name: Annotated[str, Field("", description="Name of the inverter controller.")]
    capacity: Annotated[
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
    def example(cls) -> "InverterEquipment":
        """Example for load model."""
        return InverterEquipment(
            capacity=PositiveApparentPower(3.8, "kva"),
            rise_limit=ActivePowerPUTime(1.1, "kW/minute"),
            fall_limit=ActivePowerPUTime(1.1, "kW/minute"),
        )
