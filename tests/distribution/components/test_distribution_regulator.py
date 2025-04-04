import pytest

from gdm.distribution.components import DistributionRegulator


def test_regulator_with_unequal_windings_and_contollers():
    with pytest.raises(ValueError):
        reg = DistributionRegulator.example()
        DistributionRegulator(
            name=reg.name,
            buses=reg.buses,
            winding_phases=reg.winding_phases,
            equipment=reg.equipment,
            controllers=[],
        )
