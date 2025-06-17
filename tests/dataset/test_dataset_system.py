"""Module testing dataset system."""

import datetime
import pytest

from pydantic import ValidationError

from gdm.quantities import Current, Distance, ResistancePULength
from gdm.distribution.equipment import BareConductorEquipment
from gdm.dataset.dataset_system import DatasetSystem
from gdm.dataset.cost_model import CostModel


@pytest.fixture(name="dataset_system")
def sample_dataset_system(tmp_path):
    """Pytest fixture for creating dataset system."""
    sys = DatasetSystem()
    yield sys

    json_file = tmp_path / "test_system.json"
    sys.to_json(json_file)
    sys.from_json(json_file)


def test_dataset_system(dataset_system):
    """Test dataset system."""

    new_cost1 = CostModel(
        name="cost-1",
        purchase_date=datetime.datetime.now(datetime.timezone.utc),
        capital_dollars=2345.5,
    )
    new_conductor = BareConductorEquipment(
        name="24_AWGSLD_Copper",
        conductor_diameter=Distance(0.0201, "in"),
        conductor_gmr=Distance(0.00065, "ft"),
        ampacity=Current(1, "ampere"),
        ac_resistance=ResistancePULength(151.62, "ohm/m"),
        dc_resistance=ResistancePULength(151.62, "ohm/m"),
        emergency_ampacity=Current(1, "ampere"),
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
    assert isinstance(
        CostModel.example(), CostModel
    ), "CostModel must return an istance of a CostModel"
    with pytest.raises(ValidationError):
        CostModel(
            purchase_date=datetime.datetime.now(datetime.timezone.utc),
            capital_dollars=234.45,
            operating_dollars=10.0,
        )
