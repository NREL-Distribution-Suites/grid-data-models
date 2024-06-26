""" This module contains class for creating graph representation of Distribution System."""

import networkx as nx
from infrasys import System

from gdm import (
    DistributionTransformerBase,
    DistributionBranchBase,
    DistributionBus,
)


def build_graph_from_system(system: System) -> nx.Graph:
    """Returns networkx instance of the system."""

    graph = nx.Graph()
    node: DistributionBus
    for node in system.get_components(DistributionBus):
        graph.add_node(node.name)

    edges: list[DistributionBranchBase | DistributionTransformerBase] = list(
        system.get_components(DistributionBranchBase)
    ) + list(system.get_components(DistributionTransformerBase))

    for edge in edges:
        graph.add_edge(
            edge.buses[0].name,
            edge.buses[1].name,
            **{"name": edge.name, "type": edge.__class__.__name__},
        )
    return graph
