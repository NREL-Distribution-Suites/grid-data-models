"""This module contains load equipment."""

from typing import Annotated

from infrasys import Component
from pydantic import Field

from gdm.distribution.equipment.phase_load_equipment import PhaseLoadEquipment
from gdm.distribution.distribution_enum import ConnectionType


class LoadEquipment(Component):
    """Interface for load model."""

    phase_loads: Annotated[
        list[PhaseLoadEquipment], Field(..., description="List of phase loads.")
    ]
    connection_type: Annotated[
        ConnectionType,
        Field(ConnectionType.STAR, description="Connection type for multi phase load."),
    ]

    @classmethod
    def example(cls) -> "LoadEquipment":
        """Example for load model."""
        phase_loads = [PhaseLoadEquipment.example()] * 3
        return LoadEquipment(
            name="Load Eqiup 1",
            phase_loads=phase_loads,
            connection_type=ConnectionType.STAR,
        )
