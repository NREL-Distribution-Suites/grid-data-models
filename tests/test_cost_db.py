import pytest

from gdm.cost.cost_models import (
    CableCost,
    CapacitorCost,
    ConductorCost,
    TransformerCost,
    VoltageRegulatorCost,
    RecloserCost,
    SwitchCost,
    FuseCost,
    FeederCost,
    SubstationCost,
)
from gdm.cost.sql_interface import SQLiteCostDB


@pytest.fixture
def sqlite_instance(tmp_path):
    sqlite_file_name = tmp_path / "test.sqlite"
    with SQLiteCostDB(sqlite_file_name) as db_instance:
        yield db_instance


COST_CLASSES = [
    TransformerCost,
    ConductorCost,
    CableCost,
    VoltageRegulatorCost,
    CapacitorCost,
    RecloserCost,
    SwitchCost,
    FuseCost,
    FeederCost,
    SubstationCost,
]


@pytest.mark.parametrize("cost_type", COST_CLASSES)
def test_cost_classes(sqlite_instance, cost_type):
    sample = cost_type.example()
    sqlite_instance.add_cost(sample)
    costs = sqlite_instance.get_costs(cost_type)

    assert isinstance(costs, list), f"{costs=} must be of type list."
    assert len(costs) == 1, f"{costs} must have one element."

    cost = sqlite_instance.get_cost(cost_type, costs[0].id)

    assert isinstance(cost, cost_type), f"{cost=} must of type {cost_type.__class__}"
