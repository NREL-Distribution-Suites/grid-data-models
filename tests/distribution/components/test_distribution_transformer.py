import pytest

from gdm import DistributionTransformer, Phase


def test_unequal_phase_length():
    with pytest.raises(ValueError):
        tr = DistributionTransformer.example()
        DistributionTransformer(
            name=tr.name,
            buses=tr.buses,
            winding_phases=[[Phase.A]],
            equipment=tr.equipment,
        )
