from typing import Annotated
from abc import ABC

from pydantic import model_validator, Field

from gdm.distribution.components.base.distribution_branch_base import DistributionBranchBase


class DistributionSwitchBase(DistributionBranchBase, ABC):
    """Interface for distribution branch that can be toggled."""

    is_closed: Annotated[list[bool], Field(description="Status of branch for each phase.")]

    @model_validator(mode="after")
    def validate_fields(self) -> "DistributionSwitchBase":
        """Custom validator for distribution switch."""
        if len(self.is_closed) != len(self.phases):
            msg = f"Length of {self.is_closed=} must be equal to length of {self.phases=}"
            raise ValueError(msg)
