import pytest
import networkx as nx

from gdm.distribution.components import DistributionLoad
from .get_sample_system import get_three_bus_system


@pytest.fixture
def create_system():
    """Creates a dummy system."""
    sys = get_three_bus_system()
    yield sys


def test_distribution_graph(create_system):
    """Tests distribution graph."""
    graph_instance = create_system.get_undirected_graph()
    assert isinstance(graph_instance, nx.Graph)
    assert isinstance(
        create_system.get_bus_connected_components("Bus-3", DistributionLoad)[0], DistributionLoad
    )
