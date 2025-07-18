"""This module contains distribution branch."""

from typing import Annotated
from itertools import product
from abc import ABC
import math

from pydantic import model_validator, Field

from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.enums import Phase
from gdm.distribution.components.base.distribution_component_base import (
    InServiceDistributionComponentBase,
)
from gdm.quantities import Distance
from gdm.constants import PINT_SCHEMA


class DistributionBranchBase(InServiceDistributionComponentBase, ABC):
    """Data model for abstract base distribution branch."""

    buses: Annotated[
        list[DistributionBus],
        Field(..., description="List of buses connecting a branch."),
    ]
    length: Annotated[Distance, PINT_SCHEMA, Field(..., description="Length of the branch.", gt=0)]
    phases: Annotated[
        list[Phase],
        Field(..., description="List of phases in the same order as conductors."),
    ]

    @model_validator(mode="after")
    def validate_fields_base(self) -> "DistributionBranchBase":
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

        if not math.isclose(
            self.buses[0].rated_voltage.magnitude,
            self.buses[1].rated_voltage.magnitude,
            rel_tol=0.001,  # 10^-3
        ):
            msg = (
                f"From bus {self.buses[0].rated_voltage=}"
                f"and to bus voltage {self.buses[1].rated_voltage=} rating should be same."
            )
            raise ValueError(msg)

        if len(self.phases) != len(set(self.phases)):
            msg = f"Duplicate phases not allowed for conductors {self.phases=}"
            raise ValueError(msg)

        return self
