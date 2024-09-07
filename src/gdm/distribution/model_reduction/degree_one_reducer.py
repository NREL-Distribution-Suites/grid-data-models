import networkx as nx

from gdm.distribution.model_reduction.abstract_reducer import AbstractReducer
from gdm import (
    MatrixImpedanceSwitchEquipment,
    MatrixImpedanceBranchEquipment,
    DistributionTransformerBase,
    DistributionVoltageSource,
    DistributionCapacitor,
    MatrixImpedanceSwitch,
    MatrixImpedanceBranch,
    DistributionSystem,
    DistributionSolar,
    DistributionLoad,
    DistributionBus,
)


def remove_keys_from_dict(model_dict: dict, key_names: list[str] = ["name", "uuid"]) -> dict:
    for key_name in key_names:
        if key_name in model_dict:
            model_dict.pop(key_name)
        for k, v in model_dict.items():
            if isinstance(v, dict):
                model_dict[k] = remove_keys_from_dict(v)
            elif isinstance(v, list):
                values = []
                for value in v:
                    if isinstance(value, dict):
                        value = remove_keys_from_dict(value)
                    values.append(value)
                    model_dict[k] = values
    return model_dict


class DegreeOneReducer(AbstractReducer):
    def __init__(self, distribution_system: DistributionSystem) -> None:
        super().__init__(distribution_system)

    def build(
        self,
        reduced_system: DistributionSystem = DistributionSystem(
            auto_add_composed_components=True, name="reduced_model"
        ),
    ) -> DistributionSystem:
        one_degree_subgraphs = self._graph.subgraph(
            [
                node
                for node in self._graph.nodes()
                if self._tree.in_degree(node) == 1 and self._tree.out_degree(node) in [0, 1]
            ]
        )

        reduced_network = self._graph.copy()
        for _, c in enumerate(nx.connected_components(one_degree_subgraphs)):
            if len(c) > 2:
                one_degree_lateral: nx.DiGraph = self._tree.subgraph(c)
                unfrozen_one_degree_lateral = nx.Graph(one_degree_lateral)
                for u, v in one_degree_lateral.edges():
                    component = self._distribution_system.get_component(
                        self._graph.edges[u, v]["type"], self._graph.edges[u, v]["name"]
                    )
                    if isinstance(component, DistributionTransformerBase):
                        unfrozen_one_degree_lateral.remove_edge(u, v)
                self._build_merged_branches(unfrozen_one_degree_lateral, reduced_network, reduced_system)
                
                
        for u, v in reduced_network.edges():
            if self._graph.has_edge(u, v):
                component = self._distribution_system.get_component(
                    self._graph.edges[u, v]["type"], self._graph.edges[u, v]["name"]
                )
                reduced_system.add_component(component)

        loads = self._distribution_system.get_components(DistributionLoad)
        solars = self._distribution_system.get_components(DistributionSolar)
        capacitors = self._distribution_system.get_components(DistributionCapacitor)
        sources = self._distribution_system.get_components(DistributionVoltageSource)

        reduced_system.add_components(*loads)
        reduced_system.add_components(*solars)
        reduced_system.add_components(*sources)
        reduced_system.add_components(*capacitors)

        reduced_system.info()
        return reduced_system

    def _build_merged_branches(self, unfrozen_one_degree_lateral, reduced_network, reduced_system):
    
        for _, e in enumerate(nx.connected_components(unfrozen_one_degree_lateral)):
            if len(e) > 2:
                one_degree_sub_lateral: nx.DiGraph = self._tree.subgraph(e)

                equipments = []
                component = None
                length = 0
                for u, v in one_degree_sub_lateral.edges():
                    component = self._distribution_system.get_component(
                        self._graph.edges[u, v]["type"], self._graph.edges[u, v]["name"]
                    )
                    equipments.append(
                        remove_keys_from_dict(component.equipment.model_dump())
                    )
                    length += component.length

                if all(equipments):
                    n12 = self.get_lateral_end_nodes(one_degree_sub_lateral)
                    buses_to_be_removed = set(one_degree_sub_lateral.nodes()).difference(
                        n12
                    )
                    loads = []
                    for bus in buses_to_be_removed:
                        loads.extend(
                            self._distribution_system.get_bus_connected_components(
                                bus, DistributionLoad
                            )
                        )
                    if len(loads) == 0:
                        reduced_network.remove_nodes_from(buses_to_be_removed)
                        reduced_network.add_edge(*n12)
                        buses: list[DistributionBus] = [
                            self._distribution_system.get_component(DistributionBus, b)
                            for b in n12
                        ]

                        if isinstance(component.equipment, MatrixImpedanceSwitchEquipment):
                            branch = MatrixImpedanceSwitch(
                                name=f"{n12[0]}__{n12[1]}",
                                buses=buses,
                                length=length,
                                phases=buses[1].phases,
                                equipment=component.equipment,
                                is_closed=[True for phase in buses[1].phases],
                            )
                        elif isinstance(
                            component.equipment, MatrixImpedanceBranchEquipment
                        ):
                            branch = MatrixImpedanceBranch(
                                name=f"{n12[0]}__{n12[1]}",
                                buses=buses,
                                length=length,
                                phases=buses[1].phases,
                                equipment=component.equipment,
                            )
                        else:
                            raise NotImplementedError(
                                "Equipment type not currently supported"
                            )
                        reduced_system.add_component(branch)


    def get_lateral_end_nodes(self, lateral: nx.Graph):
        lateral_end_node = None
        lateral_start_node = None
        for node in lateral.nodes():
            if lateral.out_degree(node) == 1 and lateral.in_degree(node) == 0:
                lateral_start_node = node
            if lateral.out_degree(node) == 0 and lateral.in_degree(node) == 1:
                lateral_end_node = node
        return [lateral_start_node, lateral_end_node]
