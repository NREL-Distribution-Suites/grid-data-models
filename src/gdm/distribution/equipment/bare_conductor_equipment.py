""" This module contains bare conductor equipment."""

from typing import Annotated, Optional

from infrasys import Component
from pydantic import Field

from gdm.distribution.limitset import ThermalLimitSet
from gdm.quantities import (
    PositiveResistancePULength,
    PositiveDistance,
    PositiveCurrent,
)
from gdm.constants import PINT_SCHEMA


class BareConductorEquipment(Component):
    """Interface for conductor catalaog."""

    conductor_diameter: Annotated[
        PositiveDistance, PINT_SCHEMA, Field(..., description="Diameter of the conductor.")
    ]
    conductor_gmr: Annotated[
        PositiveDistance,
        PINT_SCHEMA,
        Field(..., description="Geometric mean radius of the conductor."),
    ]
    ampacity: Annotated[
        PositiveCurrent, PINT_SCHEMA, Field(..., description="Ampacity of the conductor.")
    ]
    ac_resistance: Annotated[
        PositiveResistancePULength,
        PINT_SCHEMA,
        Field(
            ...,
            description="Per unit length positive alternating current resistance of the conductor.",
        ),
    ]
    emergency_ampacity: Annotated[
        PositiveCurrent,
        PINT_SCHEMA,
        Field(..., description="Emergency ampacity for this conductor."),
    ]
    dc_resistance: Annotated[
        PositiveResistancePULength,
        PINT_SCHEMA,
        Field(
            ...,
            description="Per unit length positive direct current resistance of the conductor.",
        ),
    ]
    loading_limit: Annotated[
        Optional[ThermalLimitSet],
        Field(None, description="Loading limit set for this conductor."),
    ]

    @classmethod
    def example(cls) -> "BareConductorEquipment":
        """Example for bare conductor."""
        return BareConductorEquipment(
            name="24_AWGSLD_Copper",
            conductor_diameter=PositiveDistance(0.0201, "in"),
            conductor_gmr=PositiveDistance(0.00065, "ft"),
            ampacity=PositiveCurrent(1, "ampere"),
            ac_resistance=PositiveResistancePULength(151.62, "ohm/m"),
            dc_resistance=PositiveResistancePULength(151.62, "ohm/m"),
            emergency_ampacity=PositiveCurrent(1, "ampere"),
        )
