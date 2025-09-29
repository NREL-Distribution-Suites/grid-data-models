from uuid import uuid4

from gdm.distribution.components import DistributionVoltageSource, DistributionBus
from gdm.exceptions import MultipleOrEmptyVsourceFound
from gdm.distribution import DistributionSystem

import pytest


def test_distribution_graph_multiple_edges(simple_distribution_system: DistributionSystem):
    """Tests distribution graph."""
    system = simple_distribution_system.deepcopy()
    system.auto_add_composed_components = True

    buses = sorted(system.get_components(DistributionBus), key=lambda x: x.name)

    v_source = DistributionVoltageSource.example()
    v_source_copy = v_source.model_copy(update={"uuid": uuid4(), "bus": buses[4]})
    system.add_component(v_source_copy)
    with pytest.raises(MultipleOrEmptyVsourceFound):
        system.get_source_bus()
