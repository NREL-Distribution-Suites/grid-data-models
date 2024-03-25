"""This module contains sequence impedance branch."""

from typing import Annotated

from pydantic import Field, model_validator

from gdm.distribution.components.distribution_branch import DistributionBranch
from gdm.distribution.equipment.sequence_impedance_branch_equipment import (
    SequenceImpedanceBranchEquipment,
)


class SequenceImpedanceBranch(DistributionBranch):
    """Interface for sequence impedance branch."""

    equipment: Annotated[
        SequenceImpedanceBranchEquipment, Field(..., description="Sequence impedance branch.")
    ]

    @model_validator(mode="after")
    def validate_fields(self) -> "SequenceImpedanceBranch":
        """Custom validator for sequence impedance branch."""
        if len(self.phases) == 1:
            msg = f"Sequence impedance assigned to single phase {self.phases=}"
            raise ValueError(msg)
        return self

    @classmethod
    def example(cls) -> "SequenceImpedanceBranch":
        """Example for sequence impedance branch."""
        base_branch = DistributionBranch.example()
        return SequenceImpedanceBranch(
            buses=base_branch.buses,
            length=base_branch.length,
            phases=base_branch.phases,
            name=base_branch.name,
            equipment=SequenceImpedanceBranchEquipment.example(),
        )
