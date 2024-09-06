from pathlib import Path

from loguru import logger
import networkx as nx

from gdm.distribution.components.base.distribution_transformer_base import (
    DistributionTransformerBase,
)
from gdm.distribution.model_reduction.abstract_reducer import AbstractReducer
from gdm.distribution.model_reduction.abstract_reducer import LumpedComponent
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.distribution_system import DistributionSystem


class PrimaryModel(AbstractReducer):
  
    def __init__(self, distribution_system: DistributionSystem) -> None:
        super().__init__(distribution_system)
    

    def build(
        self, 
        reduced_system : DistributionSystem = DistributionSystem(
            auto_add_composed_components = True,
            name = "reduced_model"
            )
        ) -> DistributionSystem:
        all_subtree_buses = []
        components: dict[str, LumpedComponent] = {}

        primary_buses = [
            bus.name
            for bus in self._distribution_system.get_components(
                DistributionBus,
                filter_func=lambda x: x.nominal_voltage.to("kilovolt").magnitude > 1.0,
            )
        ]

        logger.info(f"Number of primary buses identified: {len(primary_buses)}")
        primary_network = self._graph.subgraph(primary_buses)
        logger.info("Building primary skeleton")
        reduced_system: DistributionSystem = self._build_reduced_network_skeleton(
            reduced_system,
            primary_network
        )
        logger.info("Primary skeleton build complete")

        distribution_xfmr_hv_buses = set(
            [
                (xfmr.buses[0].name, xfmr.buses[1].name)
                for xfmr in self._distribution_system.get_components(
                    DistributionTransformerBase,
                    filter_func=lambda x: x.buses[1].nominal_voltage.to("kilovolt").magnitude < 1.0
                    and x.buses[0].nominal_voltage.to("kilovolt").magnitude > 1.0,
                )
            ]
        )
        logger.info(
            f"Number of HV distribution transformer buses identified: {len(distribution_xfmr_hv_buses)}"
        )

        for i, xfmr_buses in enumerate(distribution_xfmr_hv_buses):
            primary_bus, secondary_bus = xfmr_buses
            logger.info(
                f"Primary lump load complete: {i / len(distribution_xfmr_hv_buses) * 100.0}"
            )
            subgraph = self._graph.subgraph(nx.descendants(self._tree, secondary_bus))
            logger.info(
                f"Secondary subgraph size: {len(subgraph.nodes())} nodes and {len(subgraph.edges())} edges"
            )
            all_subtree_buses.extend(list(subgraph.nodes))
            components[primary_bus] = self._build_lumped_components(subgraph)
            
        reduced_system = self._add_lumped_components_to_primary(reduced_system, components)
        return reduced_system
