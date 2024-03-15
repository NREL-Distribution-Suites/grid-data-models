""" This module contains class for creating graph representation of Distribution System."""

import re

import networkx as nx
from infrasys.component_models import Component

from gdm.distribution.distribution_system import DistributionSystem
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.components.distribution_branch import DistributionBranch
from gdm.distribution.components.distribution_transformer import DistributionTransformer


def get_component_attr(component_type: Component):
    # Use regular expression to find uppercase letters and insert '_' before them
    # Then convert the whole string to lowercase
    return re.sub(r"(?<!^)(?=[A-Z])", "_", component_type.__class__.__name__).lower()


class DistributionGraph:
    def __init__(self, system: DistributionSystem):
        """constructor for the distribution graph module.
        Args:
            distribution_model (DistributionModel): instance of the distribution model
        """

        self.system = system
        self.graph_model = nx.Graph()
        self._add_nodes(self.system.get_components(DistributionBus))
        self._add_edges(self.system.get_components(DistributionBranch))
        self._add_edges(self.system.get_components(DistributionTransformer))

    @property
    def graph(self):
        """Method to return graph instance."""
        return self.graph_model

    def get_node_components(
        self, component_type: Component, node_name: str
    ) -> list[Component] | None:
        """Get components from graph node."""
        return self.graph_model.nodes[node_name].get(get_component_attr(component_type))

    def _get_bus_connected_components(self, bus_name: str) -> dict[str, list[Component]]:
        """Returns list of components by class type."""

        connected_components: dict[str, list[Component]] = {}
        for component_type in self.system.components.get_types():
            if "bus" in component_type.model_fields:
                filtered_components = list(
                    filter(
                        lambda x: x.bus.name == bus_name,
                        self.system.get_components(component_type),
                    )
                )
                if filtered_components:
                    key_name = get_component_attr(component_type)
                    connected_components[key_name] = filtered_components

        return connected_components

    def _add_nodes(self, nodes: list[DistributionBus]):
        """Method to add nodes."""
        for node in nodes:
            key_name = get_component_attr(node)
            self.graph_model.add_node(
                node.name, **{key_name: node}, **self._get_bus_connected_components(node.name)
            )

    def _add_edges(self, edges: list[DistributionBranch | DistributionTransformer]):
        """Method to add edges."""

        for edge in edges:
            key_name = get_component_attr(edge)
            self.graph_model.add_edge(edge.buses[0].name, edge.buses[1].name, **{key_name: edge})
