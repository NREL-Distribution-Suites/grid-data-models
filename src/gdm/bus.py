""" Interface for power system bus."""

from typing import Annotated, Optional

from infrasys import Component, Location
from pydantic import Field

from gdm.quantities import PositiveVoltage


class PowerSystemBus(Component):
    """Interface for power system bus."""

    nominal_voltage: Annotated[
        PositiveVoltage, Field(..., description="Nominal voltage for this bus.")
    ]
    coordinate: Annotated[
        Optional[Location],
        Field(None, description="Coordinate for the power system bus."),
    ]

    @classmethod
    def example(cls) -> "PowerSystemBus":
        return PowerSystemBus(
            name="Bus1",
            nominal_voltage=PositiveVoltage(400, "volt"),
            coordinate=Location(x=20.0, y=30.0),
        )
