""" This module contains matrix impedance switch equipment."""

from typing import Optional
from typing_extensions import Annotated

from pydantic import Field

from gdm.distribution.equipment.matrix_impedance_branch_equipment import (
    MatrixImpedanceBranchEquipment,
)
from gdm.distribution.controllers.distribution_switch_controller import (
    DistributionSwitchController,
)


class MatrixImpedanceSwitchEquipment(MatrixImpedanceBranchEquipment):
    """Interface for matrix impedance based recloser equipment."""

    controller: Annotated[
        Optional[DistributionSwitchController],
        Field(None, description="Optional controller for this switch."),
    ]

    @classmethod
    def example(cls) -> "MatrixImpedanceSwitchEquipment":
        """Example for matrix impedance switch equipment."""
        return MatrixImpedanceSwitchEquipment(
            **MatrixImpedanceBranchEquipment.example().model_dump(exclude_none=True)
        )
