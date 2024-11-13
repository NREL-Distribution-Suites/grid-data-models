"""This module contains distribution system."""

from typing import Type

from infrasys import Component, System
from infrasys.time_series_models import SingleTimeSeries

import networkx as nx
import pandas as pd

import gdm
from gdm.distribution.components.base.distribution_branch_base import (
    DistributionBranchBase,
)
from gdm.distribution.components.base.distribution_transformer_base import (
    DistributionTransformerBase,
)
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.components.distribution_load import DistributionLoad
from gdm.distribution.components.distribution_solar import DistributionSolar
from gdm.distribution.components.distribution_transformer import (
    DistributionTransformer,
)
from gdm.distribution.components.distribution_vsource import (
    DistributionVoltageSource,
)
from gdm.distribution.distribution_enum import Phase
from gdm.exceptions import (
    MultipleOrEmptyVsourceFound,
    NoComponentsFoundError,
    NoTimeSeriesDataFound,
    TimeseriesVariableDoesNotExist,
    UnsupportedVariableError,
)


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

    def get_combined_solar_timeseries(
        self, solars: list[DistributionSolar], var_name: str
    ) -> SingleTimeSeries:
        """Method to return combined solar time series data.

        Parameters
        ----------
        solars: list[DistributionSolar]
            List of solar for aggregating timeseries data.
        var_name: str
            Name of the time series variable.

        Returns
        -------
        SingleTimeSeries
        """

        if var_name not in ["irradiance"]:
            msg = f"{var_name=} is not supported for solar timeseries aggregation."
            raise UnsupportedVariableError(msg)
        ts_components = [
            self.get_time_series(solar, var_name) * solar.equipment.rated_capacity
            for solar in solars
        ]
        ts_comp_type = {type(ts_comp) for ts_comp in ts_components}
        if len(ts_comp_type) != 1:
            msg = f"Multiple time series data type aggregation not supported: {ts_comp_type}"
            raise TypeError(msg)

        return ts_comp_type.pop().aggregate(ts_components, "avg")

    def get_combined_load_timeseries(
        self, loads: list[DistributionLoad], var_name: str
    ) -> SingleTimeSeries:
        """Method to return combined load time series data.

        Parameters
        ----------
        loads: list[DistributionLoad]
            List of loads for aggregating timeseries data.
        var_name: str
            Name of the time series variable.

        Returns
        -------
        SingleTimeSeries
        """
        if var_name not in ["active_power", "reactive_power"]:
            msg = f"{var_name=} is not supported for load timeseries aggregation."
            raise UnsupportedVariableError(msg)
        ts_components = [self.get_time_series(load, var_name) for load in loads]
        ts_comp_type = {type(ts_comp) for ts_comp in ts_components}
        if len(ts_comp_type) != 1:
            msg = f"Multiple time series data type aggregation not supported: {ts_comp_type}"
            raise TypeError(msg)
        return ts_comp_type.pop().aggregate(ts_components, "sum")

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

    def get_combined_timeseries_df(
        self,
        component_type: Type[Component],
        variables: list[str] | None = None,
        unit_conversion: dict[str, str] | None = None,
    ) -> pd.DataFrame:
        """
        Method for returning combined timeseries dataframe for given component type.

        Parameters
        ----------
        component_type: Type[Component]
            Component type.
        variables: list[str] | None, optional
            List of variables to combine. If None, all available variables will be combined.
        unit_conversion: dict[str, str] | None, optional
            Optional dictionary to perform unit conversion on data in pint quantities.

        Returns
        -------
        pd.DataFrame

        Raises
        ------
        NoComponentsFoundError
            If no components of the specified type are found.
        NoTimeSeriesDataFound
            If no timeseries data is found for a component.
        TypeError
            If timeseries data is not of type SingleTimeSeries.
        TimeseriesVariableDoesNotExist
            If specified variables do not exist for the given component.
        """
        dfs = []
        components = list(self.get_components(component_type))
        if not components:
            raise NoComponentsFoundError(
                f"No components of type {component_type} found in {self.name}"
            )

        for component in components:
            ts_metadata = self.list_time_series_metadata(component)
            if not ts_metadata:
                msg = f"No timeseries data found for {component=}"
                raise NoTimeSeriesDataFound(msg)
            avail_vars = {md.variable_name for md in ts_metadata}
            selected_vars = variables or avail_vars

            if variables and not set(variables).issubset(avail_vars):
                missing_vars = set(variables) - avail_vars
                msg = f"Timeseries variables {missing_vars} do not exist for {component}. Available variables are {avail_vars}."
                raise TimeseriesVariableDoesNotExist(msg)

            for var in selected_vars:
                ts_data = self.get_time_series(component, variable_name=var)
                if not isinstance(ts_data, SingleTimeSeries):
                    msg = f"Unsupported type for time series data: {type(ts_data)}"
                    raise TypeError(msg)

                if unit_conversion and var in unit_conversion:
                    converted_data = ts_data.data.__class__(
                        ts_data.data.to_numpy(), ts_data.data.units
                    ).to(unit_conversion[var])
                    unit = unit_conversion[var]
                else:
                    converted_data = ts_data.data
                    unit = ts_data.data.units if hasattr(ts_data.data, "units") else None

                dfs.append(
                    pd.DataFrame(
                        {
                            "timestamp": [
                                ts_data.initial_time + idx * ts_data.resolution
                                for idx in range(ts_data.length)
                            ],
                            "variable_name": [var] * ts_data.length,
                            "component_uuid": [component.uuid] * ts_data.length,
                            "value": converted_data,
                            "units": [unit] * ts_data.length,
                        }
                    )
                )

        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
