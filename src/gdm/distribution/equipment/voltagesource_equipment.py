"""This module contains interface for distribution substation."""

from typing import Annotated

from infrasys import Component
from pydantic import Field

from gdm.distribution.equipment.phase_voltagesource_equipment import PhaseVoltageSourceEquipment


class VoltageSourceEquipment(Component):
    """Interface for voltage source model."""

    sources: Annotated[
        list[PhaseVoltageSourceEquipment],
        Field(
            ...,
            description="list of single phase voltage sources",
        ),
    ]

    @classmethod
    def example(cls) -> "VoltageSourceEquipment":
        """Example for voltage source model."""
        return VoltageSourceEquipment(
            name="Voltage Source 1", sources=[PhaseVoltageSourceEquipment.example()] * 3
        )
