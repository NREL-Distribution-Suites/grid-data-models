from pathlib import Path

from loguru import logger
import networkx as nx

from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.distribution_system import DistributionSystem
from infrasys.exceptions import ISNotStored

from gdm.distribution.model_reduction.abstract_reducer import AbstractReducer
from gdm.distribution.model_reduction.abstract_reducer import LumpedComponent
from gdm import Phase

class ThreePhaseBalancedReduction(AbstractReducer):
    def __init__(self, distribution_system: DistributionSystem):
        super().__init__(distribution_system)

    def build(
        self, 
        reduced_system : DistributionSystem = DistributionSystem(
            auto_add_composed_components = True,
            name = "reduced_model"
            )
        ) -> DistributionSystem:
        components = {}

        three_phases_buses = set(
            [
                Phase.A,
                Phase.B,
                Phase.C,
            ]
        )
        primary_buses = [
            bus.name
            for bus in self._distribution_system.get_components(
                DistributionBus,
                filter_func=lambda x: three_phases_buses.issubset(x.phases)
                and x.nominal_voltage.to("kilovolt").magnitude > 1.0,
            )
        ]
        primary_network = self._graph.subgraph(primary_buses)
        primary_tree = nx.dfs_tree(primary_network, source=self._source_buses[0])
        reduced_system: DistributionSystem = self._build_reduced_network_skeleton(
            reduced_system,
            primary_network
        )
        
        primary_leaf_buses = set(
            [
                x
                for x in primary_tree.nodes()
                if primary_tree.out_degree(x) != self._tree.out_degree(x)
            ]
        )

        for i, primary_bus in enumerate(primary_leaf_buses):
            
            logger.info(f"Primary lump load complete: {i / len(primary_leaf_buses) * 100.0}")

            edges_on_complete_system = set(self._graph.edges(primary_bus))
            edges_on_primary_system = set(primary_network.edges(primary_bus))

            edges_removed = edges_on_complete_system.difference(edges_on_primary_system)
            subgraphs = nx.Graph()
            for from_node, to_node in edges_removed:
                subgraph = self._graph.subgraph(nx.descendants(self._tree, to_node))
                logger.info(
                    f"Secondary subgraph size: {len(subgraph.nodes())} nodes and {len(subgraph.edges())} edges"
                )
                subgraphs = nx.union(subgraphs, subgraph)

            components[primary_bus] = self._build_lumped_components(subgraphs)
           
        reduced_system = self._add_lumped_components_to_primary(reduced_system, components)
        return reduced_system
