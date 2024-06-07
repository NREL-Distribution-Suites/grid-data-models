import pytest

from gdm import MatrixImpedanceBranch, DistributionBus, Phase


def test_wrong_number_of_buses():
    branch = MatrixImpedanceBranch.example()
    with pytest.raises(ValueError):
        MatrixImpedanceBranch(
            name=branch.name,
            buses=branch.buses + [DistributionBus.example()],
            length=branch.length,
            phases=branch.phases,
            equipment=branch.equipment,
        )


def test_wrong_phase_connection():
    branch = MatrixImpedanceBranch.example()
    with pytest.raises(ValueError):
        MatrixImpedanceBranch(
            name=branch.name,
            buses=branch.buses,
            length=branch.length,
            phases=[Phase.S1, Phase.A, Phase.B],
            equipment=branch.equipment,
        )


def test_same_from_and_to_bus():
    branch = MatrixImpedanceBranch.example()
    with pytest.raises(ValueError):
        MatrixImpedanceBranch(
            name=branch.name,
            buses=[branch.buses[0], branch.buses[0]],
            length=branch.length,
            phases=branch.phases,
            equipment=branch.equipment,
        )


def test_duplicate_phases():
    branch = MatrixImpedanceBranch.example()
    with pytest.raises(ValueError):
        MatrixImpedanceBranch(
            name=branch.name,
            buses=branch.buses,
            length=branch.length,
            phases=[Phase.A, Phase.A, Phase.B],
            equipment=branch.equipment,
        )
