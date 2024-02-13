"""Module testing dataset system."""

from datetime import datetime
from gdm.quantities import PositiveCurrent, PositiveDistance, PositiveResistancePULength

import pytest

from gdm.dataset.dataset_system import DatasetSystem
from gdm.dataset.cost_model import CostModel
from gdm import BareConductorEquipment


@pytest.fixture
def dataset_system(tmp_path):
    """Pytest fixture for creating dataset system."""
    sys = DatasetSystem()
    yield sys

    json_file = tmp_path / "test_system.json"
    sys.to_json(json_file)
    sys.from_json(json_file)


def test_dataset_system(dataset_system):
    """Test dataset system."""

    new_cost1 = CostModel(name="cost-1", purchase_date=datetime.utcnow(), capital_dollars=2345.5)
    new_conductor = BareConductorEquipment(
        name="24_AWGSLD_Copper",
        conductor_diameter=PositiveDistance(0.0201, "in"),
        conductor_gmr=PositiveDistance(0.00065, "ft"),
        ampacity=PositiveCurrent(1, "ampere"),
        ac_resistance=PositiveResistancePULength(151.62, "ohm/m"),
        dc_resistance=PositiveResistancePULength(151.62, "ohm/m"),
        emergency_ampacity=PositiveCurrent(1, "ampere"),
    )
    dataset_system.add_component(new_conductor)
    dataset_system.add_cost(
        catalog=dataset_system.get_component(BareConductorEquipment, name="24_AWGSLD_Copper"),
        cost=new_cost1,
    )
    costs = dataset_system.get_costs(
        dataset_system.get_component(BareConductorEquipment, name="24_AWGSLD_Copper")
    )
    assert len(costs) == 1, f"Length of costs {costs=} must be 1"
    assert isinstance(costs[0], CostModel), f"Cost instance must be of type CostModel {costs=}"
