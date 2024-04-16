""" This module contains interface for power system capacitor."""

# pylint:disable=pointless-statement

from typing import Annotated

from pydantic import Field, NonNegativeInt, PositiveInt, model_validator

from infrasys import Component
from gdm.quantities import PositiveReactivePower
from gdm.constants import PINT_SCHEMA


class PowerSystemCapacitor(Component):
    """Interface for power system capacitor."""

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
    def validate_fields(self) -> "PowerSystemCapacitor":
        """Custom validator for fields."""
        if self.num_banks < self.num_banks_on:
            msg = f"Status {self.num_banks_on} must be less than or equal"
            f"to number of banks. {self.num_banks}"
            raise ValueError(msg)

        return self

    @classmethod
    def example(cls) -> "PowerSystemCapacitor":
        """Example for power system capacitor."""
        return PowerSystemCapacitor(
            name="Phase-Cap-1",
            rated_capacity=PositiveReactivePower(200, "kvar"),
            num_banks_on=1,
            num_banks=1,
        )
