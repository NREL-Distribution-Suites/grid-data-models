from io import StringIO

from loguru import logger
import networkx as nx
import pytest

from gdm.distribution.components import DistributionLoad, DistributionBus, MatrixImpedanceSwitch
from .get_sample_system import get_three_bus_system
from gdm.distribution import DistributionSystem


@pytest.fixture
def create_system():
    """Creates a dummy system."""
    sys = get_three_bus_system()
    yield sys


def test_distribution_graph(create_system: DistributionSystem):
    """Tests distribution graph."""
    graph_instance = create_system.get_undirected_graph()
    assert isinstance(graph_instance, nx.Graph)
    assert isinstance(
        create_system.get_bus_connected_components("Bus-3", DistributionLoad)[0], DistributionLoad
    )


def test_distribution_graph_directed_no_additional_model_removed(
    simple_distribution_system: DistributionSystem,
):
    """Tests distribution graph."""

    system = simple_distribution_system.deepcopy()
    system.auto_add_composed_components = True

    buses = sorted(system.get_components(DistributionBus), key=lambda x: x.name)
    switch = MatrixImpedanceSwitch.example()
    switch.buses = [buses[0], buses[4]]
    switch.is_closed = [False, False, False]
    system.add_component(switch)

    graph_instance = system.get_directed_graph(False)
    assert graph_instance.number_of_nodes() == 21
    assert graph_instance.number_of_edges() == 21
    assert graph_instance.has_edge(switch.buses[0].name, switch.buses[1].name)

    log_stream = StringIO()
    logger.add(log_stream, level="WARNING")

    graph_instance = system.get_directed_graph(True)
    assert graph_instance.number_of_nodes() == 21
    assert graph_instance.number_of_edges() == 20
    assert not graph_instance.has_edge(switch.buses[0].name, switch.buses[1].name)

    log_contents = log_stream.getvalue()
    assert "| WARNING  |" not in log_contents


def test_distribution_graph_directed_additional_model_removed(
    simple_distribution_system: DistributionSystem,
):
    """Tests distribution graph."""

    system = simple_distribution_system.deepcopy()
    system.auto_add_composed_components = True

    buses = sorted(system.get_components(DistributionBus), key=lambda x: x.name)
    switch = MatrixImpedanceSwitch.example()
    switch.buses = [buses[0], buses[4]]
    switch.is_closed = [True, True, True]
    system.add_component(switch)

    graph_instance = system.get_directed_graph(False)
    assert graph_instance.number_of_nodes() == 21
    assert graph_instance.number_of_edges() == 21
    assert graph_instance.has_edge(switch.buses[0].name, switch.buses[1].name)

    log_stream = StringIO()
    logger.add(log_stream, level="WARNING")

    graph_instance = system.get_directed_graph(True)
    assert graph_instance.number_of_nodes() == 21
    assert graph_instance.number_of_edges() == 20

    log_contents = log_stream.getvalue()
    assert "| WARNING  |" in log_contents
