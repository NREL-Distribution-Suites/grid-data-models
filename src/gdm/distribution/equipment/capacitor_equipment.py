""" This module contains capacitor equipment."""

from typing import Annotated

from infrasys import Component
from pydantic import Field

from gdm.distribution.equipment.phase_capacitor_equipment import PhaseCapacitorEquipment
from gdm.distribution.distribution_enum import ConnectionType, VoltageTypes
from gdm.quantities import PositiveVoltage, PositiveFrequency
from gdm.constants import PINT_SCHEMA


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

    nominal_voltage: Annotated[
        PositiveVoltage,
        PINT_SCHEMA,
        Field(..., description="Nominal voltage rating for this capacitor."),
    ]
    voltage_type: Annotated[
        VoltageTypes,
        Field(..., description="Set voltage type for nominal voltage."),
    ]
    nominal_frequency: Annotated[
        PositiveFrequency,
        PINT_SCHEMA,
        Field(PositiveFrequency(60, "hertz"), description="Nominal frequency for this capacitor."),
    ]

    @classmethod
    def example(cls) -> "CapacitorEquipment":
        """Example for capacitor model."""
        return CapacitorEquipment(
            name="capacitor-equipment-1",
            phase_capacitors=[PhaseCapacitorEquipment.example()] * 3,
            connection_type=ConnectionType.STAR,
            nominal_voltage=PositiveVoltage(7.2, "kilovolt"),
            voltage_type=VoltageTypes.LINE_TO_GROUND,
            nominal_frequency=PositiveFrequency(60, "hertz"),
        )
