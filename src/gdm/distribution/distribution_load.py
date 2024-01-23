""" This module contains interface for distribution load."""
from typing import Annotated, Optional

from infrasys.component_models import Component, ComponentWithQuantities
from pydantic import PositiveInt, model_validator, Field

from gdm.distribution.distribution_component import DistributionComponent
from gdm.distribution.distribution_bus import DistributionBus
from gdm.distribution.distribution_enum import Phase
from gdm.load import PowerSystemLoad
from gdm.quantities import PositiveVoltage


class PhaseLoad(Component):
    """Interface for phase loads."""

    phase: Annotated[Phase, Field(..., description="Phase to which this is connected to.")]
    load: Annotated[
        PowerSystemLoad,
        Field(..., description="PowerSystemLoad instance for this phase load."),
    ]

    @classmethod
    def example(cls) -> "PhaseLoad":
        return PhaseLoad(phase=Phase.A, load=PowerSystemLoad.example())


class DistributionLoad(ComponentWithQuantities):
    """Interface for distribution load."""

    bus: Annotated[
        DistributionBus,
        Field(
            ...,
            description="Distribution bus to which this load is connected to.",
        ),
    ]
    belongs_to: Annotated[
        Optional[DistributionComponent],
        Field(None, description="Provides info about substation and feeder."),
    ]
    phase_loads: Annotated[list[PhaseLoad], Field(..., description="List of phase loads.")]
    num_customers: Annotated[
        Optional[PositiveInt],
        Field(None, description="Number of customers for this load"),
    ]

    @model_validator(mode="after")
    def validate_fields(self) -> "DistributionLoad":
        load_phs = [lo.phase for lo in self.phase_loads]
        if not set(load_phs).issubset(set(self.bus.phases)):
            msg = f"Loads phases {load_phs} must be subset of bus phases. {self.bus.phases}"
            raise ValueError(msg)
        return self

    @classmethod
    def example(cls) -> "DistributionLoad":
        return DistributionLoad(
            name="DistributionLoad1",
            bus=DistributionBus(
                voltage_type="line-to-ground",
                name="Bus1",
                phases=[Phase.A],
                nominal_voltage=PositiveVoltage(0.4, "kilovolt"),
            ),
            phase_loads=[PhaseLoad(phase=Phase.A, load=PowerSystemLoad.example())],
        )
