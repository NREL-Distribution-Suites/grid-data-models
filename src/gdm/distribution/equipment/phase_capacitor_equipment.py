"""This module contains phase capacitor equipment."""

from typing import Annotated
import uuid

from pydantic import Field, NonNegativeInt, PositiveInt, model_validator
from infrasys import Component

from gdm.quantities import (
    PositiveResistance,
    PositiveReactance,
    PositiveReactivePower,
)
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
    rated_reactive_power: Annotated[
        PositiveReactivePower,
        PINT_SCHEMA,
        Field(..., description="Capacity of this capacitor."),
    ]
    num_banks_on: Annotated[
        NonNegativeInt, Field(..., description="Number of banks currently on.")
    ]
    num_banks: Annotated[PositiveInt, Field(1, description="Number of banks in the capacitor.")]

    @classmethod
    def split(
        cls, instance: "PhaseCapacitorEquipment", num_splits: int
    ) -> "PhaseCapacitorEquipment":
        return instance.model_copy(
            update={
                "name": str(uuid.uuid4()),
                "rated_reactive_power": instance.rated_reactive_power / num_splits,
                "resistance": instance.resistance * num_splits,
                "reactance": instance.reactance * num_splits,
            }
        )

    @classmethod
    def aggregate(
        cls, instances: list["PhaseCapacitorEquipment"], name: str
    ) -> "PhaseCapacitorEquipment":
        return PhaseCapacitorEquipment(
            name=name,
            rated_reactive_power=sum(inst.rated_reactive_power for inst in instances),
            resistance=1
            / sum(1 / inst.resistance if inst.resistance.magnitude else 0 for inst in instances),
            reactance=1
            / sum(1 / inst.reactance if inst.reactance.magnitude else 0 for inst in instances),
            num_banks=sum(inst.num_banks for inst in instances),
            num_banks_on=sum(inst.num_banks_on for inst in instances),
        )

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
            rated_reactive_power=PositiveReactivePower(200, "kvar"),
            num_banks=1,
            num_banks_on=1,
        )
