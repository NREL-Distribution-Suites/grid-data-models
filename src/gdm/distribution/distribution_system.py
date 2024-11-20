"""This module contains distribution system."""

from typing import Annotated, Type

from infrasys import Component, System
from infrasys.time_series_models import SingleTimeSeries, SingleTimeSeriesMetadata
from infrasys.normalization import NormalizationMax, NormalizationByValue

import networkx as nx
import pandas as pd
from pint import Quantity
from pydantic import BaseModel, Field
import numpy as np
from numpy.typing import NDArray

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
    InconsistentTimeseriesAggregation,
    MultipleOrEmptyVsourceFound,
    NoComponentsFoundError,
    NoTimeSeriesDataFound,
    TimeseriesVariableDoesNotExist,
    UnsupportedVariableError,
)
from gdm.quantities import PositiveActivePower


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


def _get_timeseries_actual_data(ts_data: SingleTimeSeries) -> NDArray | Quantity:
    if ts_data.normalization is None:
        return ts_data.data
    elif isinstance(ts_data.normalization, NormalizationMax):
        return ts_data.data * ts_data.normalization.max_value
    elif isinstance(ts_data.normalization, NormalizationByValue):
        return ts_data.data * ts_data.normalization.value
    else:
        msg = f"Unspported type of normalization {type(ts_data.normalization)=}"
        raise TypeError(msg)


def _get_load_power(
    load: DistributionLoad, ts_data: SingleTimeSeries, metadata: SingleTimeSeriesMetadata
) -> list[float]:
    """Internal function to return time series data in kw"""
    user_attr = UserAttributes.model_validate(metadata.user_attributes)
    denormalized_data = _get_timeseries_actual_data(ts_data)
    if user_attr.use_actual:
        return denormalized_data

    match metadata.variable_name:
        case "active_power":
            return denormalized_data * sum(
                [ph_load.real_power for ph_load in load.equipment.phase_loads]
            )
        case "reactive_power":
            return denormalized_data * sum(
                [ph_load.reactive_power for ph_load in load.equipment.phase_loads]
            )
        case _:
            msg = f"{metadata.variable_name} is not supported for load power calculation."
            raise UnsupportedVariableError(msg)


def _get_solar_power(
    solar: DistributionSolar, ts_data: SingleTimeSeries, _: SingleTimeSeriesMetadata
) -> list[float]:
    """Internal function to return time series data in kw"""
    denormalized_data = _get_timeseries_actual_data(ts_data)
    dc_power = denormalized_data.to("kilowatt/m^2").magnitude * solar.equipment.solar_power.to(
        "kilowatts"
    )
    return np.clip(
        dc_power,
        a_min=PositiveActivePower(0, dc_power.units),
        a_max=solar.equipment.rated_capacity.to("kilova"),
    )
    # TODO: Looks like GDM is not capturing irradiance which is why user_attr is not used
    # this will work fine if irradiance=1 however if it is different than 1 then
    # in case use_actual is false needs to be multiplied with this value.


COMPONENT_TO_POWER_MAPPER = {
    DistributionLoad: _get_load_power,
    DistributionSolar: _get_solar_power,
}


def _check_for_timeseries_metadata_consistency(ts_metadata: list[SingleTimeSeriesMetadata]):
    # Extract unique properties from ts_data

    user_attrs = [
        UserAttributes.model_validate(metadata.user_attributes) for metadata in ts_metadata
    ]
    unique_props = {
        "profile_type": {user_attr.profile_type for user_attr in user_attrs},
        "profile_name": {user_attr.profile_name for user_attr in user_attrs},
    }

    # Validate uniformity across properties
    if any(len(prop) != 1 for prop in unique_props.values()):
        inconsistent_props = {k: v for k, v in unique_props.items() if len(v) > 1}
        msg = f"Inconsistent timeseries data: {inconsistent_props}"
        raise InconsistentTimeseriesAggregation(msg)


def _check_for_timeseries_consistency(ts_data: list[SingleTimeSeries]):
    # Extract unique properties from ts_data
    unique_props = {
        "length": {data.length for data in ts_data},
        "resolution": {data.resolution for data in ts_data},
        "start_time": {data.initial_time for data in ts_data},
        "variable": {data.variable_name for data in ts_data},
        "data_type": {type(data.data) for data in ts_data},
    }

    # Validate uniformity across properties
    if any(len(prop) != 1 for prop in unique_props.values()):
        inconsistent_props = {k: v for k, v in unique_props.items() if len(v) > 1}
        msg = f"Inconsistent timeseries data: {inconsistent_props}"
        raise InconsistentTimeseriesAggregation(msg)


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
            Variable name for which to combine timeseries data.

        Returns
        -------
        SingleTimeSeries
        """

        if var_name not in ["irradiance"]:
            msg = f"{var_name=} is not supported for solar timeseries aggregation."
            raise UnsupportedVariableError(msg)
        ts_components: list[SingleTimeSeries] = [
            self.get_time_series(solar, var_name) for solar in solars
        ]
        _check_for_timeseries_consistency(ts_components)
        new_data = [
            _get_timeseries_actual_data(ts_data) * solar.equipment.solar_power
            for ts_data, solar in zip(ts_components, solars)
        ]
        return SingleTimeSeries(
            data=sum(new_data) / len(new_data),
            variable_name=var_name,
            normalization=None,
            initial_time=ts_components[0].initial_time,
            resolution=ts_components[0].resolution,
        )

    def get_combined_load_timeseries(
        self, loads: list[DistributionLoad], var_name: str
    ) -> SingleTimeSeries:
        """Method to return combined load time series data.

        Parameters
        ----------
        loads: list[DistributionLoad]
            List of loads for aggregating timeseries data.
        var_name: str
            Variable name used for time series aggregation.

        Returns
        -------
        SingleTimeSeries
        """
        ts_components: list[SingleTimeSeries] = [
            self.get_time_series(load, var_name) for load in loads
        ]
        _check_for_timeseries_consistency(ts_components)
        ts_metadata = list[SingleTimeSeriesMetadata] = [
            self.list_time_series_metadata(load, var_name)[0] for load in loads
        ]
        _check_for_timeseries_metadata_consistency(ts_metadata)
        ts_load_data = [
            _get_load_power(load, ts_data, metadata)
            for load, ts_data, metadata in zip(loads, ts_components, ts_metadata)
        ]
        return SingleTimeSeries(
            data=sum(ts_load_data),
            variable_name=var_name,
            normalization=None,
            initial_time=ts_components[0].initial_time,
            resolution=ts_components[0].resolution,
        )

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
        if unit_conversion is None:
            unit_conversion = {}
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
                ts_data: SingleTimeSeries = self.get_time_series(component, variable_name=var)
                metadata = [meta for meta in ts_metadata if meta.variable_name == var][0]
                power_data = COMPONENT_TO_POWER_MAPPER[type(component)](
                    component, ts_data, metadata
                )
                dfs.append(
                    pd.DataFrame(
                        {
                            "timestamp": [
                                ts_data.initial_time + idx * ts_data.resolution
                                for idx in range(ts_data.length)
                            ],
                            "variable_name": [var] * ts_data.length,
                            "component_uuid": [component.uuid] * ts_data.length,
                            "value": (
                                power_data.to(unit_conversion[var])
                                if var in unit_conversion
                                else power_data
                            ),
                            "units": [
                                unit_conversion[var]
                                if var in unit_conversion
                                else power_data.units
                            ]
                            * ts_data.length,
                        }
                    )
                )

        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
