"""This module contains interface for distribution substation."""

from typing import Annotated

from infrasys import Component
from infrasys.quantities import Angle, Resistance, Voltage
from pydantic import Field

from gdm.quantities import Reactance, PositiveVoltage
from gdm.constants import PINT_SCHEMA


class PhaseVoltageSourceEquipment(Component):
    """Data model for phase voltage source."""

    r0: Annotated[Resistance, PINT_SCHEMA, Field(..., description="Zero sequence resistance.")]
    r1: Annotated[Resistance, PINT_SCHEMA, Field(..., description="Positive sequence resistance.")]
    x0: Annotated[Reactance, PINT_SCHEMA, Field(..., description="Zero sequence reactance.")]
    x1: Annotated[Reactance, PINT_SCHEMA, Field(..., description="Positive sequence reactane.")]
    voltage: Annotated[
        Voltage, PINT_SCHEMA, Field(..., description="Voltage for this substation.")
    ]
    angle: Annotated[Angle, PINT_SCHEMA, Field(..., description="Angle for the voltage")]

    @classmethod
    def example(cls) -> "PhaseVoltageSourceEquipment":
        """Example for phase voltage source."""
        return PhaseVoltageSourceEquipment(
            name="phase-source-1",
            r0=Resistance(0.001, "ohm"),
            r1=Resistance(0.001, "ohm"),
            x0=Reactance(0.001, "ohm"),
            x1=Reactance(0.001, "ohm"),
            voltage=PositiveVoltage(132.0, "kilovolt"),
            angle=Angle(180, "degree"),
        )
