"""This module contains distribution system."""

from typing import Annotated, Type

from infrasys import Component, System
import networkx as nx
from pydantic import BaseModel, Field


import gdm
from gdm.distribution.components.base.distribution_branch_base import (
    DistributionBranchBase,
)
from gdm.distribution.components.base.distribution_transformer_base import (
    DistributionTransformerBase,
)
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.components.distribution_transformer import (
    DistributionTransformer,
)
from gdm.distribution.components.distribution_vsource import (
    DistributionVoltageSource,
)
from gdm.distribution.distribution_enum import Phase
from gdm.exceptions import (
    MultipleOrEmptyVsourceFound,
)


class UserAttributes(BaseModel):
    """Interface for single time series data user attributes."""

    profile_name: Annotated[
        str, Field(..., description="Name of the profile to be used in original powerflow model.")
    ]
    profile_type: Annotated[
        str, Field(..., description="Type of profile could be PMult, QMult etc.")
    ]
    use_actual: Annotated[
        bool,
        Field(..., description="Boolean flag indicating whether these values are actual or not."),
    ]


class DistributionSystem(System):
    """Class interface for distribution system."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_format_version = gdm.distribution.__version__

    def get_bus_connected_components(
        self, bus_name: str, component_type: Component
    ) -> list[Component] | None:
        """Returns list of components connected to this bus."""

        if "bus" in component_type.model_fields:
            return list(
                filter(
                    lambda x: x.bus.name == bus_name,
                    self.get_components(component_type),
                )
            )
        elif "buses" in component_type.model_fields:
            return list(
                filter(
                    lambda x: bus_name in [bus.name for bus in x.buses],
                    self.get_components(component_type),
                )
            )

    def get_model_types_with_field_type(
        self, field_type: Type[Component]
    ) -> list[Type[Component]]:
        return [
            model_type
            for model_type in self.get_component_types()
            if any(
                [field.annotation == field_type for _, field in model_type.model_fields.items()]
            )
        ]

    def get_source_bus(self) -> DistributionBus:
        voltage_sources = self.get_components(DistributionVoltageSource)
        buses = [v_source.bus for v_source in voltage_sources]
        if len(buses) != 1:
            msg = f"Multiple or no vsource found for this system {buses}."
            raise MultipleOrEmptyVsourceFound(msg)
        return buses[0]

    def get_undirected_graph(self) -> nx.Graph:
        graph = nx.Graph()
        node: DistributionBus
        for node in self.get_components(DistributionBus):
            graph.add_node(node.uuid)

        edges: list[DistributionBranchBase | DistributionTransformerBase] = list(
            self.get_components(DistributionBranchBase)
        ) + list(self.get_components(DistributionTransformerBase))

        for edge in edges:
            graph.add_edge(
                edge.buses[0].uuid,
                edge.buses[1].uuid,
                **{"name": edge.name, "type": edge.__class__},
            )
        return graph

    def get_subsystem(
        self, bus_uuids: list[str], name: str, keep_timeseries: bool = False
    ) -> "DistributionSystem":
        """Method to get subsystem from list of buses.

        Parameters
        ----------
        bus_uuids: list[str]
            List of bus uuids.
        name: str
            Name of the subsystem.
        keep_timeseries: bool
            Set this flag to retain timeseries data associated with the component.

        Returns
        -------
        DistributionSystem
        """
        tree = self.get_directed_graph()
        subtree = tree.subgraph(bus_uuids)
        bus_uuids = set(bus_uuids)
        subtree_system = DistributionSystem(auto_add_composed_components=True, name=name)
        for u, v, _ in subtree.edges(data=True):
            parent_components = self.list_parent_components(
                self.get_component_by_uuid(u)
            ) + self.list_parent_components(self.get_component_by_uuid(v))
            for component in parent_components:
                if isinstance(
                    component,
                    (DistributionBranchBase, DistributionTransformerBase),
                ):
                    nodes = {bus.uuid for bus in component.buses}
                    if not nodes.issubset(bus_uuids):
                        continue
                if not subtree_system.has_component(component):
                    subtree_system.add_component(component)
        if keep_timeseries:
            for comp in subtree_system.get_components(
                Component, filter_func=lambda x: self.has_time_series(x)
            ):
                ts_metadata = self.list_time_series_metadata(comp)
                for metadata in ts_metadata:
                    ts_data = self.get_time_series(comp, metadata.variable_name)
                    subtree_system.add_time_series(ts_data, comp, **metadata.user_attributes)

        return subtree_system

    def get_directed_graph(self) -> nx.DiGraph:
        ugraph = self.get_undirected_graph()
        return nx.dfs_tree(ugraph, source=self.get_source_bus().uuid)

    def get_split_phase_mapping(self) -> dict[str, set[Phase]]:
        split_phase_map = {}
        original_tree = self.get_directed_graph()
        split_phase_trs: list[DistributionTransformer] = list(
            self.get_components(
                DistributionTransformer,
                filter_func=lambda x: x.equipment.is_center_tapped,
            )
        )
        for tr in split_phase_trs:
            lv_bus = {
                bus.uuid for bus in tr.buses if Phase.S1 in bus.phases or Phase.S2 in bus.phases
            }.pop()
            hv_bus = (set([bus.uuid for bus in tr.buses]) - set([lv_bus])).pop()
            lv_system = self.get_subsystem(
                list(nx.descendants(original_tree, lv_bus)) + [lv_bus], name=""
            )
            bus_model_types = self.get_model_types_with_field_type(DistributionBus)
            for model_type in bus_model_types:
                for asset in lv_system.get_components(model_type):
                    split_phase_map[asset.uuid] = set(self.get_component_by_uuid(hv_bus).phases)
        return split_phase_map

    @classmethod
    def merge(cls, subsystems: list["DistributionSystem"]) -> "DistributionSystem":
        system = DistributionSystem(auto_add_composed_components=True)
        for subsystem in subsystems:
            components = list(subsystem.iter_all_components())
            system.add_components(*components)
        return system
