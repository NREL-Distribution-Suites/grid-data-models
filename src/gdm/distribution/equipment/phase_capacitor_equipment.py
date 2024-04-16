"""This module contains phase capacitor equipment."""

from typing import Annotated

from pydantic import Field

from gdm.capacitor import PowerSystemCapacitor
from gdm.quantities import PositiveResistance, PositiveReactance
from gdm.constants import PINT_SCHEMA


class PhaseCapacitorEquipment(PowerSystemCapacitor):
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

    @classmethod
    def example(cls) -> "PhaseCapacitorEquipment":
        """Example for phase capacitor equipment."""
        base_cap = PowerSystemCapacitor.example()
        return PhaseCapacitorEquipment(
            name=base_cap.name,
            rated_capacity=base_cap.rated_capacity,
            num_banks=base_cap.num_banks,
            num_banks_on=base_cap.num_banks_on,
        )
