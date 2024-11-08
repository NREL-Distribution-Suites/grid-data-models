"""This module contains distribution system."""

from datetime import date
from typing import Type

from infrasys import Component, System
from rich.console import Console
from rich.table import Table
from loguru import logger
import networkx as nx


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
from gdm.exceptions import MultipleOrEmptyVsourceFound
from gdm.temporal_models import ModelUpdates, TemporalUpdates


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

    def get_subsystem(self, bus_uuids: list[str], name: str) -> "DistributionSystem":
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

    def apply_updates_at_timestamp(self, date: date, update_scenario: str):
        self.update_log = []
        scenario: ModelUpdates = self.get_component(ModelUpdates, update_scenario)
        for update in scenario.updates:
            if update.date <= date:
                logger.info(f"Modification applied at timestamp: {update.date}")
                self.update_temporal_component_addition(update)
                self.update_temporal_component_deletion(update)
                self.update_temporal_component_edit(update)
        self.system_update_info(scenario)

    def update_temporal_component_addition(self, update: TemporalUpdates):
        for addition in update.additions:
            c: Component = addition.component
            self.add_component(c)
            self.update_log.append(
                [str(update.date), "Addition", str(c.uuid), c.__class__.__name__, c.name]
            )

    def update_temporal_component_deletion(self, update: TemporalUpdates):
        for deltetion in update.deletions:
            c: Component = self.get_component_by_uuid(deltetion.component_uuid)
            self.remove_component(c)
            self.update_log.append(
                [str(update.date), "Deletion", str(c.uuid), c.__class__.__name__, c.name]
            )

    def update_temporal_component_edit(self, update: TemporalUpdates):
        for edit in update.edits:
            c: Component = self.get_component_by_uuid(edit.component_uuid)
            component_parameters = list(c.model_fields.keys())

            for parameter, value in edit.component_parameters.items():
                if parameter not in component_parameters:
                    raise KeyError(
                        f"{parameter} is not a valid parameter for model type {c.__class__.__name__}"
                    )
                setattr(c, parameter, value)
                self.update_log.append(
                    [str(update.date), "Edit", str(c.uuid), c.__class__.__name__, c.name]
                )
            self.get_component_by_uuid(edit.component_uuid)

    def system_update_info(self, scenario: ModelUpdates):
        table = Table(title=f"Updates applied to system from scenario '{scenario.name}'")
        table.add_column("Timestamp", justify="right", style="cyan", no_wrap=True)
        table.add_column("Operation", style="magenta")
        table.add_column("UUID", justify="right", style="bright_magenta")
        table.add_column("Component Type", justify="right", style="cyan")
        table.add_column("Component Name", justify="right", style="green")

        for log in self.update_log:
            table.add_row(*log)

        console = Console()
        console.print(table)
