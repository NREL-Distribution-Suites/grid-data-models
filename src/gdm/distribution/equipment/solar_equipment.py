"""This module contains solar equipment. """

from typing import Annotated

from infrasys import Component
from pydantic import Field

from gdm.quantities import PositiveActivePower
from gdm.distribution.curve import Curve
from gdm.constants import PINT_SCHEMA


class SolarEquipment(Component):
    """Interface for Solar Model."""

    rated_power: Annotated[
        PositiveActivePower,
        PINT_SCHEMA,
        Field(..., description="Maximum power of the PV array for 1.0 kW/m^2 irradiance."),
    ]
    power_temp_curve: Annotated[
        Curve | None,
        Field(None, description="The power temperature curve for the PV array."),
    ]
    resistance: Annotated[
        float,
        Field(
            ...,
            strict=True,
            ge=0,
            le=100,
            description="Percentage internal resistance for the PV array.",
        ),
    ]
    reactance: Annotated[
        float,
        Field(
            ...,
            strict=True,
            ge=0,
            le=100,
            description="Percentage internal reactance for the PV array.",
        ),
    ]

    @classmethod
    def example(cls) -> "SolarEquipment":
        "Example for a solar Equipment"
        return SolarEquipment(
            name="solar-install1",
            rated_power=PositiveActivePower(4, "kW"),
            power_temp_curve=None,
            resistance=50,
            reactance=0,
        )
