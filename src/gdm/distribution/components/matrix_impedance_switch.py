"""This module contains matrix impedance switch."""

from typing import Annotated

from pydantic import Field, model_validator

from gdm.distribution.equipment.matrix_impedance_switch_equipment import (
    MatrixImpedanceSwitchEquipment,
)
from gdm.distribution.components.distribution_switch import DistributionSwitch


class MatrixImpedanceSwitch(DistributionSwitch):
    """Interface for matrix impedance switch."""

    equipment: Annotated[
        MatrixImpedanceSwitchEquipment,
        Field(..., description="Matrix impedance branch equipment."),
    ]

    @model_validator(mode="after")
    def validate_fields(self) -> "MatrixImpedanceSwitch":
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
    def example(cls) -> "MatrixImpedanceSwitch":
        """Example for matrix impedance branch."""
        return MatrixImpedanceSwitch(
            **DistributionSwitch.example().model_dump(exclude_none=True),
            equipment=MatrixImpedanceSwitchEquipment.example(),
        )
