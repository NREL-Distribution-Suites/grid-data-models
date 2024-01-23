"""This module contains interface for distribution substation."""
from typing import Annotated

from infrasys.component_models import Component
from infrasys.quantities import Angle, Resistance, Voltage
from pydantic import BaseModel, Field

from gdm.quantities import Reactance, PositiveVoltage
from gdm.distribution.distribution_bus import DistributionBus
from gdm.distribution.distribution_enum import Phase


class PhaseVoltageSource(Component):
    phase: Annotated[Phase, Field(..., description="Phase to which this is connected to.")]
    r0: Annotated[Resistance, Field(..., description="Zero sequence resistance.")]
    r1: Annotated[Resistance, Field(..., description="Positive sequence resistance.")]
    x0: Annotated[Reactance, Field(..., description="Zero sequence reactance.")]
    x1: Annotated[Reactance, Field(..., description="Positive sequence reactane.")]
    voltage: Annotated[Voltage, Field(..., description="Voltage for this substation.")]
    angle: Annotated[Angle, Field(..., description="Angle for the voltage")]

    @classmethod
    def example(cls) -> "PhaseVoltageSource":
        return PhaseVoltageSource(
            phase=Phase.A,
            r0=Resistance(0.001, "ohm"),
            r1=Resistance(0.001, "ohm"),
            x0=Reactance(0.001, "ohm"),
            x1=Reactance(0.001, "ohm"),
            voltage=PositiveVoltage(132.0, "kilovolt"),
            angle=Angle(180, "degree"),
        )


class DistributionVoltageSource(BaseModel):
    """Interface for distribution substation."""

    bus: Annotated[
        DistributionBus,
        Field(
            ...,
            description="Distribution bus to which this voltage source is connected to.",
        ),
    ]
    phase_voltage_sources: Annotated[
        list[PhaseVoltageSource],
        Field(
            ...,
            description="list of single phase voltage sources",
        ),
    ]

    @classmethod
    def example(cls) -> "DistributionVoltageSource":
        return DistributionVoltageSource(
            name="DistributionVoltageSource1",
            bus=DistributionBus.example(),
            phase_voltage_sources=[PhaseVoltageSource.example()],
        )
