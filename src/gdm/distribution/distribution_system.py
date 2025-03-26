"""This module contains distribution system."""

from typing import Annotated, Type
import importlib.metadata

from infrasys.time_series_models import TimeSeriesData, SingleTimeSeries
from infrasys import Component, System
from pydantic import BaseModel, Field
import networkx as nx

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
        self.data_format_version = importlib.metadata.version("grid-data-models")

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
            graph.add_node(node.name)

        edges: list[DistributionBranchBase | DistributionTransformerBase] = list(
            self.get_components(DistributionBranchBase)
        ) + list(self.get_components(DistributionTransformerBase))

        for edge in edges:
            graph.add_edge(
                edge.buses[0].name,
                edge.buses[1].name,
                **{"name": edge.name, "type": edge.__class__},
            )
        return graph

    def _add_to_subsystem(
        self,
        subtree_system: "DistributionSystem",
        parent_components: list[Component],
        bus_names: list[DistributionBus],
    ):
        for component in parent_components:
            if isinstance(
                component,
                (DistributionBranchBase, DistributionTransformerBase),
            ):
                nodes = {bus.name for bus in component.buses}
                if not nodes.issubset(set(bus_names)):
                    continue
            if not subtree_system.has_component(component):
                subtree_system.add_component(component)

    def get_subsystem(
        self,
        bus_names: list[str],
        name: str,
        keep_timeseries: bool = False,
        time_series_type: Type[TimeSeriesData] = SingleTimeSeries,
    ) -> "DistributionSystem":
        """Method to get subsystem from list of buses.

        Parameters
        ----------
        bus_names: list[str]
            List of bus names
        name: str
            Name of the subsystem.
        keep_timeseries: bool
            Set this flag to retain timeseries data associated with the component.
        time_series_type: Type[TimeSeriesData]
            Type of time series data. Defaults to: SingleTimeSeries
        Returns
        -------
        DistributionSystem
        """
        tree = self.get_directed_graph()
        subtree = tree.subgraph(bus_names)
        subtree_system = DistributionSystem(auto_add_composed_components=True, name=name)
        for u, v, _ in subtree.edges(data=True):
            parent_components = self.list_parent_components(
                self.get_component(DistributionBus, u)
            ) + self.list_parent_components(self.get_component(DistributionBus, v))
            self._add_to_subsystem(subtree_system, parent_components, bus_names)

        for u in subtree.nodes():
            parent_components = self.list_parent_components(self.get_component(DistributionBus, u))
            self._add_to_subsystem(subtree_system, parent_components, bus_names)

        if keep_timeseries:
            for comp in subtree_system.get_components(
                Component,
                filter_func=lambda x: self.has_time_series(x, time_series_type=time_series_type),
            ):
                ts_metadata = self.list_time_series_metadata(
                    comp, time_series_type=time_series_type
                )
                for metadata in ts_metadata:
                    ts_data = self.get_time_series(
                        comp, metadata.variable_name, time_series_type=time_series_type
                    )
                    subtree_system.add_time_series(ts_data, comp, **metadata.user_attributes)

        return subtree_system

    def get_directed_graph(self) -> nx.DiGraph:
        ugraph = self.get_undirected_graph()
        return nx.dfs_tree(ugraph, source=self.get_source_bus().name)

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
                bus.name for bus in tr.buses if Phase.S1 in bus.phases or Phase.S2 in bus.phases
            }.pop()
            hv_bus = (set([bus.name for bus in tr.buses]) - set([lv_bus])).pop()
            lv_system = self.get_subsystem(
                list(nx.descendants(original_tree, lv_bus)) + [lv_bus], name=""
            )
            bus_model_types = self.get_model_types_with_field_type(DistributionBus)
            for model_type in bus_model_types:
                for asset in lv_system.get_components(model_type):
                    split_phase_map[asset.name] = set(
                        self.get_component(DistributionBus, hv_bus).phases
                    )
        return split_phase_map
