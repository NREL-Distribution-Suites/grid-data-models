""" This module contains matrix impedance branch equipment."""

from gdm.distribution.equipment.base.matrix_impedance_branch_equipment_base import (
    MatrixImpedanceBranchEquipmentBase,
)
from gdm.quantities import (
    CapacitancePULength,
    ResistancePULength,
    ReactancePULength,
    PositiveCurrent,
)

class MatrixImpedanceBranchEquipment(MatrixImpedanceBranchEquipmentBase):
    @classmethod
    def example(cls) -> "MatrixImpedanceBranchEquipment":
        """Example for matrix impedance model."""
        return MatrixImpedanceBranchEquipment(
            name="matrix-impedance-branch-1",
            r_matrix=ResistancePULength(
                [
                    [0.08820, 0.0312137, 0.0306264],
                    [0.0312137, 0.0901946, 0.0316143],
                    [0.0306264, 0.0316143, 0.0889665],
                ],
                "ohm/mi",
            ),
            x_matrix=ReactancePULength(
                [
                    [0.20744, 0.0935314, 0.0760312],
                    [0.0935314, 0.200783, 0.0855879],
                    [0.0760312, 0.0855879, 0.204877],
                ],
                "ohm/mi",
            ),
            c_matrix=CapacitancePULength(
                [
                    [2.90301, -0.679335, -0.22313],
                    [-0.679335, 3.15896, -0.481416],
                    [-0.22313, -0.481416, 2.8965],
                ],
                "nanofarad/mi",
            ),
            ampacity=PositiveCurrent(90, "ampere"),
        )
