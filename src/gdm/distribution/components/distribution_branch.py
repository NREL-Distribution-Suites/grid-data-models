""" This module contains distribution branch. """

from typing import Annotated
from itertools import product

from pydantic import model_validator, Field
from infrasys.component_models import ComponentWithQuantities

from gdm.distribution.distribution_common import BELONG_TO_TYPE
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.distribution_enum import Phase
from gdm.quantities import (
    PositiveDistance,
    PositiveVoltage,
)


class DistributionBranch(ComponentWithQuantities):
    """Interface for distribution branch."""

    belongs_to: BELONG_TO_TYPE
    buses: Annotated[
        list[DistributionBus],
        Field(..., description="List of buses connecting a branch."),
    ]
    length: Annotated[PositiveDistance, Field(..., description="Length of the branch.")]
    phases: Annotated[
        list[Phase],
        Field(..., description="List of phases in the same order as conductors."),
    ]
    is_closed: Annotated[bool, Field(True, description="Status of the line.")]

    @model_validator(mode="after")
    def validate_fields(self) -> "DistributionBranch":
        """Custom validator for base distribution branch."""
        if len(self.buses) != 2:
            msg = f"Number of buses {len(self.buses)} must be 2."
            raise ValueError(msg)

        for phase, bus in product(self.phases, self.buses):
            if phase not in bus.phases:
                msg = f"Conductor phase ({phase=}) does not match bus phases ({bus.phases=})"
                raise ValueError(msg)

        if self.buses[0].name == self.buses[1].name:
            msg = (
                f"From bus {self.buses[0].name=} and to bus"
                f"{self.buses[1].name=} should be different."
            )
            raise ValueError(msg)

        if self.buses[0].nominal_voltage != self.buses[1].nominal_voltage:
            msg = (
                f"From bus {self.buses[0].nominal_voltage=}"
                f"and to bus voltage {self.buses[1].nominal_voltage=} rating should be same."
            )
            raise ValueError(msg)

        if len(self.phases) != len(set(self.phases)):
            msg = f"Duplicate phases not allowed for conductors {self.phases=}"
            raise ValueError(msg)

        return self

    @classmethod
    def example(cls) -> "DistributionBranch":
        """Example for base distribution branch."""
        bus1 = DistributionBus(
            voltage_type="line-to-ground",
            phases=[Phase.A, Phase.B, Phase.C],
            nominal_voltage=PositiveVoltage(400, "volt"),
            name="DistBus1",
        )
        bus2 = DistributionBus(
            voltage_type="line-to-ground",
            phases=[Phase.A, Phase.B, Phase.C],
            nominal_voltage=PositiveVoltage(400, "volt"),
            name="DistBus2",
        )
        return DistributionBranch(
            buses=[bus1, bus2],
            length=PositiveDistance(130.2, "meter"),
            phases=[Phase.A, Phase.B, Phase.C],
            name="p14u405",
        )
