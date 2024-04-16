"""This module contains interface for distribution substation."""

from typing import Annotated

from infrasys import Component
from infrasys.quantities import Angle, Resistance, Voltage
from pydantic import Field

from gdm.distribution.distribution_common import BELONG_TO_TYPE
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.quantities import Reactance, PositiveVoltage
from gdm.distribution.distribution_enum import Phase
from gdm.constants import PINT_SCHEMA


class PhaseVoltageSourceEquipment(Component):
    """Interface for phase voltage source."""

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


class DistributionVoltageSource(Component):
    """Interface for distribution substation."""

    belongs_to: BELONG_TO_TYPE
    bus: Annotated[
        DistributionBus,
        Field(
            ...,
            description="Distribution bus to which this voltage source is connected to.",
        ),
    ]
    phases: Annotated[list[Phase], Field(..., description="Phase to which this is connected to.")]
    equipment: Annotated[VoltageSourceEquipment, Field(..., description="Voltage source model.")]

    @classmethod
    def example(cls) -> "DistributionVoltageSource":
        """Example for distribution voltage source."""
        return DistributionVoltageSource(
            name="DistributionVoltageSource1",
            bus=DistributionBus.example(),
            phases=[Phase.A, Phase.B, Phase.C],
            equipment=VoltageSourceEquipment.example(),
        )
