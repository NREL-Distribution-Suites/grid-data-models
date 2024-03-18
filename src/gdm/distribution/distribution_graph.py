""" This module contains class for creating graph representation of Distribution System."""

import networkx as nx
from infrasys.system import System

from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.components.distribution_branch import DistributionBranch
from gdm.distribution.components.distribution_transformer import DistributionTransformer


def build_graph_from_system(system: System) -> nx.Graph:
    """Returns networkx instance of the system."""

    graph = nx.Graph()
    for node in system.get_components(DistributionBus):
        graph.add_node(node.name)

    edges: list[DistributionBranch | DistributionTransformer] = list(
        system.get_components(DistributionBranch)
    ) + list(system.get_components(DistributionTransformer))

    for edge in edges:
        graph.add_edge(edge.buses[0].name, edge.buses[1].name)
    return graph
