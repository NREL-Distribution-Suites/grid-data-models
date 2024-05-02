"""This module contains phase capacitor equipment."""

from typing import Annotated

from pydantic import Field, NonNegativeInt, PositiveInt, model_validator
from infrasys import Component

from gdm.quantities import PositiveResistance, PositiveReactance, PositiveReactivePower
from gdm.constants import PINT_SCHEMA


class PhaseCapacitorEquipment(Component):
    """Interface for phase capacitor."""

    resistance: Annotated[
        PositiveResistance,
        PINT_SCHEMA,
        Field(
            PositiveResistance(0, "ohm"),
            description="Positive resistance for the capacitor.",
        ),
    ]
    reactance: Annotated[
        PositiveReactance,
        PINT_SCHEMA,
        Field(
            PositiveReactance(0, "ohm"),
            description="Positive reactance for the capacitor.",
        ),
    ]
    rated_capacity: Annotated[
        PositiveReactivePower,
        PINT_SCHEMA,
        Field(..., description="Capacity of this capacitor."),
    ]
    num_banks_on: Annotated[
        NonNegativeInt, Field(..., description="Number of banks currently on.")
    ]
    num_banks: Annotated[PositiveInt, Field(1, description="Number of banks in the capacitor.")]

    @model_validator(mode="after")
    def validate_fields(self) -> "PhaseCapacitorEquipment":
        """Custom validator for fields."""
        if self.num_banks < self.num_banks_on:
            msg = f"Status {self.num_banks_on} must be less than or equal"
            f"to number of banks. {self.num_banks}"
            raise ValueError(msg)

        return self

    @classmethod
    def example(cls) -> "PhaseCapacitorEquipment":
        """Example for phase capacitor equipment."""
        return PhaseCapacitorEquipment(
            name="Phase-Cap-1",
            rated_capacity=PositiveReactivePower(200,"kvar"),
            num_banks=1,
            num_banks_on=1,
        )
