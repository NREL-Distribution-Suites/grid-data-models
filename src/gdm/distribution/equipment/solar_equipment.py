"""This module contains solar equipment. """

from typing import Annotated

from infrasys import Component
from pydantic import Field

from gdm.quantities import PositiveActivePower


class SolarEquipment(Component):
    """Interface for Solar Model."""

    rated_capacity: Annotated[
        PositiveActivePower, Field(..., description="Active power rating of the Solar PV array.")
    ]

    solar_power: Annotated[
        PositiveActivePower,
        Field(..., description="The DC active power that is generated by the solar equipment."),
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

    cutout_percent: Annotated[
        float,
        Field(
            ge=0,
            le=100,
            description="If the per-unit power drops below this value the PV output is turned off.",
        ),
    ]

    cutin_percent: Annotated[
        float,
        Field(
            ge=0,
            le=100,
            description="If the per-unit power rises above this value the PV output is turned on.",
        ),
    ]

    @classmethod
    def example(cls) -> "SolarEquipment":
        "Example for a solar Equipment"
        return SolarEquipment(
            name="solar-install1",
            rated_capacity=PositiveActivePower(4, "kW"),
            solar_power=PositiveActivePower(3.2, "kW"),
            resistance=50,
            reactance=0,
            cutin_percent=25,
            cutout_percent=20,
        )