import pytest
import networkx as nx

from gdm import DistributionGraph
from gdm import DistributionLoad
from .get_sample_system import get_three_bus_system


@pytest.fixture
def create_system():
    """Creates a dummy system."""
    sys = get_three_bus_system()
    yield sys


def test_distribution_graph(create_system):
    """Tests distribution graph."""
    graph_instance = DistributionGraph(create_system)
    assert isinstance(graph_instance.graph, nx.Graph)
    assert isinstance(
        graph_instance.get_node_components(DistributionLoad, "Bus-3")[0], DistributionLoad
    )
