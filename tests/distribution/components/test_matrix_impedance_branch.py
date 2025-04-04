import pytest

from gdm.distribution.components import MatrixImpedanceBranch, DistributionBus
from gdm.quantities import PositiveVoltage
from gdm.distribution.enums import Phase


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


def test_connecting_buses_with_different_voltage():
    branch = MatrixImpedanceBranch.example()
    bus1, bus2 = branch.buses
    bus1.rated_voltage = PositiveVoltage(12.47, "kilovolts")
    bus2.rated_voltage = PositiveVoltage(12.48, "kilovolts")
    with pytest.raises(ValueError):
        MatrixImpedanceBranch(
            name=branch.name,
            buses=[bus1, bus2],
            length=branch.length,
            phases=branch.phases,
            equipment=branch.equipment,
        )
