import pytest

from gdm import MatrixImpedanceSwitch, Phase


def test_is_closed_length():
    branch = MatrixImpedanceSwitch.example()
    with pytest.raises(ValueError):
        MatrixImpedanceSwitch(
            name=branch.name,
            buses=branch.buses,
            length=branch.length,
            phases=[Phase.A, Phase.A, Phase.B],
            equipment=branch.equipment,
            is_closed=[True],
        )
