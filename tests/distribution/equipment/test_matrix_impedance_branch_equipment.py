import pytest

from gdm import MatrixImpedanceBranchEquipment


def test_matrix_impedance_branch_equipment():
    equipment = MatrixImpedanceBranchEquipment.example()
    with pytest.raises(ValueError):
        MatrixImpedanceBranchEquipment(
            name=equipment.name,
            r_matrix=equipment.r_matrix[0],
            x_matrix=equipment.x_matrix,
            c_matrix=equipment.c_matrix,
            ampacity=equipment.ampacity,
        )
