""" This module contains interface for distribution system capacitor."""
from typing import Annotated, Optional

from infrasys.component_models import Component, ComponentWithQuantities
from pydantic import Field, model_validator

from gdm.distribution.distribution_component import DistributionComponent
from gdm.distribution.distribution_bus import DistributionBus
from gdm.distribution.distribution_enum import Phase
from gdm.capacitor import PowerSystemCapacitor
from gdm.quantities import PositiveVoltage


class PhaseCapacitor(Component):
    """Interface for phase capacitor."""

    capacitor: PowerSystemCapacitor
    phase: Annotated[
        Phase,
        Field(..., description="Phase at which this capacitor is connected to."),
    ]

    @classmethod
    def example(cls) -> "PhaseCapacitor":
        return PhaseCapacitor(phase=Phase.A, capacitor=PowerSystemCapacitor.example())


class DistributionCapacitor(ComponentWithQuantities):
    """Interface for capacitor present in distribution system models."""

    bus: Annotated[
        DistributionBus,
        Field(
            ...,
            description="Distribution bus to which this capacitor is connected to.",
        ),
    ]
    belongs_to: Annotated[
        Optional[DistributionComponent],
        Field(
            None,
            description="Provides info about substation and feeder. ",
        ),
    ]
    phase_capacitors: Annotated[
        list[PhaseCapacitor],
        Field(
            ...,
            description="List of phase capacitors for this distribution capacitor.",
        ),
    ]

    @model_validator(mode="after")
    def validate_fields(self) -> "DistributionCapacitor":
        cap_phases = [cap.phase for cap in self.phase_capacitors]

        if not set(cap_phases).issubset(set(self.bus.phases)):
            msg = f"Phase capacitors phases ({cap_phases}) should be subset of bus phases"
            f" ({self.bus.phases}) to which it is connected to."
            raise ValueError(msg)
        return self

    @classmethod
    def example(cls) -> "DistributionCapacitor":
        return DistributionCapacitor(
            name="Capacitor1",
            bus=DistributionBus(
                voltage_type="line-to-ground",
                name="Bus1",
                nominal_voltage=PositiveVoltage(400, "volt"),
                phases=[Phase.A],
            ),
            phase_capacitors=[
                PhaseCapacitor(phase=Phase.A, capacitor=PowerSystemCapacitor.example())
            ],
        )
