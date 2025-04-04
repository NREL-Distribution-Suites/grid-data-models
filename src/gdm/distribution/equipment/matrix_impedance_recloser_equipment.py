"""This module contains matrix impedance recloser equipment."""

from gdm.distribution.equipment.matrix_impedance_branch_equipment import (
    MatrixImpedanceBranchEquipment,
)
from gdm.distribution.equipment.base.matrix_impedance_branch_equipment_base import (
    MatrixImpedanceBranchEquipmentBase,
)


class MatrixImpedanceRecloserEquipment(MatrixImpedanceBranchEquipmentBase):
    """Interface for matrix impedance based recloser equipment."""

    @classmethod
    def example(cls) -> "MatrixImpedanceRecloserEquipment":
        """Example for matrix impedance recloser equipment."""
        return MatrixImpedanceRecloserEquipment(
            **MatrixImpedanceBranchEquipment.example().model_dump(exclude_none=True)
        )
