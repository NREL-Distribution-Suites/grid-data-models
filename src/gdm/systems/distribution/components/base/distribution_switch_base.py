from typing import Annotated
from abc import ABC

from pydantic import model_validator, Field

from gdm.systems.distribution.components.base.distribution_branch_base import (
    DistributionBranchBase,
)


class DistributionSwitchBase(DistributionBranchBase, ABC):
    """Data model for distribution branch that can be toggled."""

    is_closed: Annotated[list[bool], Field(description="Status of branch for each conductor.")]

    @property
    def num_conductors(self) -> int:
        return len(self.phases)

    @model_validator(mode="after")
    def validate_fields_base(self) -> "DistributionSwitchBase":
        """Custom validator for distribution switch."""
        if len(self.is_closed) != self.num_conductors:
            msg = f"Length of {self.is_closed=} must equal conductor count {self.num_conductors}"
            raise ValueError(msg)
        return self
