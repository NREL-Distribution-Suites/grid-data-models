"""This module contains matrix impedance branch."""

from typing import Annotated

from pydantic import Field, model_validator

from gdm.distribution.components.distribution_branch import DistributionBranch
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.equipment.matrix_impedance_branch_equipment import (
    MatrixImpedanceBranchEquipment,
)


class MatrixImpedanceBranch(DistributionBranch):
    """Interface for matrix impedance branch."""

    equipment: Annotated[
        MatrixImpedanceBranchEquipment,
        Field(..., description="Matrix impedance branch equipment."),
    ]

    @model_validator(mode="after")
    def validate_fields(self) -> "MatrixImpedanceBranch":
        """Custom validator for matrix impedance branch."""
        for mat in [
            self.equipment.r_matrix,
            self.equipment.x_matrix,
            self.equipment.c_matrix,
        ]:
            if set(mat.shape) != {len(self.phases)}:
                msg = f"Length of matrix {mat=} did not match number of phases {self.phases=}"
                raise ValueError(msg)

        return self

    @classmethod
    def example(cls) -> "MatrixImpedanceBranch":
        """Example for matrix impedance branch."""
        base_branch = DistributionBranch.example()
        return MatrixImpedanceBranch(
            buses=base_branch.buses,
            length=base_branch.length,
            phases=base_branch.phases,
            name=base_branch.name,
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            equipment=MatrixImpedanceBranchEquipment.example(),
        )
