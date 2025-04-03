"""This module contains matrix impedance branch."""

from typing import Annotated

from pydantic import Field, model_validator

from gdm.distribution.components.base.distribution_branch_base import DistributionBranchBase
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.equipment.matrix_impedance_branch_equipment import (
    MatrixImpedanceBranchEquipment,
)
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.distribution_enum import Phase
from gdm.quantities import PositiveVoltage, PositiveDistance


class MatrixImpedanceBranch(DistributionBranchBase):
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
            ph_wo_neutral = set(self.phases) - set(Phase.N)
            if set(mat.shape) != {len(ph_wo_neutral)}:
                msg = f"Length of matrix {mat=} did not match number of phases {self.phases=}"
                raise ValueError(msg)

        return self

    @classmethod
    def example(cls) -> "MatrixImpedanceBranch":
        """Example for matrix impedance branch."""
        bus1 = DistributionBus(
            voltage_type="line-to-ground",
            phases=[Phase.A, Phase.B, Phase.C],
            rated_voltage=PositiveVoltage(400, "volt"),
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            name="Branch-DistBus1",
        )
        bus2 = DistributionBus(
            voltage_type="line-to-ground",
            phases=[Phase.A, Phase.B, Phase.C],
            rated_voltage=PositiveVoltage(400, "volt"),
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            name="Branch-DistBus2",
        )
        return MatrixImpedanceBranch(
            buses=[bus1, bus2],
            length=PositiveDistance(130.2, "meter"),
            phases=[Phase.A, Phase.B, Phase.C],
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            name="DistBranch1",
            equipment=MatrixImpedanceBranchEquipment.example(),
        )
