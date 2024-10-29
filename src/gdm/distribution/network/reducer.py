import uuid
from typing import Type

from infrasys import Component
import networkx as nx

from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.distribution_system import DistributionSystem
from gdm import Phase


def get_three_phase_buses(dist_system: DistributionSystem) -> list[str]:
    return [
        bus.uuid
        for bus in dist_system.get_components(
            DistributionBus,
            filter_func=lambda x: set((Phase.A, Phase.B, Phase.C)).issubset(x.phases),
        )
    ]


def get_aggregated_bus_component(
    subtree_system: DistributionSystem,
    bus: DistributionBus,
    model_type: Type[Component],
    split_phase_mapping: dict[str, set[Phase]],
) -> Type[Component]:
    model_components = subtree_system.get_components(model_type)

    return model_type.aggregate(
        instances=list(model_components),
        bus=bus,
        name=str(uuid.uuid4()),
        split_phase_mapping=split_phase_mapping,
    )


def reduce_to_three_phase_system(dist_system: DistributionSystem, name: str) -> DistributionSystem:
    three_phase_buses = get_three_phase_buses(dist_system)
    reduced_system = dist_system.get_subsystem(three_phase_buses, name)
    split_phase_mapping = dist_system.get_split_phase_mapping()
    original_tree = dist_system.get_directed_graph()
    three_phase_tree = original_tree.subgraph(three_phase_buses)
    for node in three_phase_tree.nodes():
        if three_phase_tree.out_degree(node) < original_tree.out_degree(node):
            sucessors_diff = set(original_tree.successors(node)) - set(
                three_phase_tree.successors(node)
            )
            successors_descendants = [
                snode
                for successor in sucessors_diff
                for snode in nx.descendants(original_tree, successor)
            ] + list(sucessors_diff)
            subtree = original_tree.subgraph(successors_descendants)
            subtree_system = dist_system.get_subsystem(subtree.nodes, "")
            model_types = subtree_system.get_model_types_with_field_type(DistributionBus)
            for model_type in model_types:
                agg_component = get_aggregated_bus_component(
                    subtree_system,
                    reduced_system.get_component_by_uuid(node),
                    model_type=model_type,
                    split_phase_mapping=split_phase_mapping,
                )
                reduced_system.add_component(agg_component)
    return reduced_system
