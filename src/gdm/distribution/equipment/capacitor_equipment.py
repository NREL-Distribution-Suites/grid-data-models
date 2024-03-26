""" This module contains capacitor equipment."""

from typing import Annotated

from infrasys import Component
from pydantic import Field

from gdm.distribution.equipment.phase_capacitor_equipment import PhaseCapacitorEquipment
from gdm.distribution.distribution_enum import ConnectionType


class CapacitorEquipment(Component):
    """Interface for capacitor model."""

    phase_capacitors: Annotated[
        list[PhaseCapacitorEquipment],
        Field(
            ...,
            description="List of phase capacitors for this distribution capacitor.",
        ),
    ]
    connection_type: Annotated[
        ConnectionType,
        Field(ConnectionType.STAR, description="Connection type for this capacitor."),
    ]

    @classmethod
    def example(cls) -> "CapacitorEquipment":
        """Example for capacitor model."""
        return CapacitorEquipment(
            name="capacitor-equipment-1",
            phase_capacitors=[PhaseCapacitorEquipment.example()] * 3,
            connection_type=ConnectionType.STAR,
        )
