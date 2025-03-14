import uuid
from typing import Type, Union, Callable

from infrasys.time_series_models import SingleTimeSeries, TimeSeriesData
import networkx as nx

from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.components.distribution_load import DistributionLoad
from gdm.distribution.components.distribution_solar import DistributionSolar
from gdm.distribution.components.distribution_battery import DistributionBattery
from gdm.distribution.distribution_system import (
    DistributionSystem,
    UserAttributes,
)
from gdm import Phase
from gdm.distribution.sys_functools import (
    get_aggregated_load_timeseries,
    get_aggregated_solar_timeseries,
    get_aggregated_battery_timeseries,
)


def get_three_phase_buses(
    dist_system: DistributionSystem,
) -> list[str]:
    return [
        bus.name
        for bus in dist_system.get_components(
            DistributionBus,
            filter_func=lambda x: set((Phase.A, Phase.B, Phase.C)).issubset(x.phases),
        )
    ]


def get_primary_buses(dist_system: DistributionSystem) -> list[str]:
    return [
        bus.name
        for bus in dist_system.get_components(
            DistributionBus,
            filter_func=lambda x: x.nominal_voltage.to("kilovolt").magnitude > 1.0,
        )
    ]


def get_aggregated_bus_component(
    subtree_system: DistributionSystem,
    bus: DistributionBus,
    model_type: DistributionLoad | DistributionSolar,
    split_phase_mapping: dict[str, set[Phase]],
) -> DistributionLoad | DistributionSolar:
    model_components = subtree_system.get_components(model_type)
    return model_type.aggregate(
        instances=list(model_components),
        bus=bus,
        name=str(uuid.uuid4()),
        split_phase_mapping=split_phase_mapping,
    )


def _reduce_system(
    dist_system: DistributionSystem,
    bus_subset: list[DistributionBus],
    name: str,
    agg_timeseries: bool = False,
    time_series_type: Type[TimeSeriesData] = SingleTimeSeries,
) -> DistributionSystem:
    reduced_system = dist_system.get_subsystem(
        bus_subset,
        name,
        keep_timeseries=agg_timeseries,
        time_series_type=time_series_type,
    )

    split_phase_mapping = dist_system.get_split_phase_mapping()
    original_tree = dist_system.get_directed_graph()
    reduced_network_tree = original_tree.subgraph(bus_subset)
    ts_agg_func_mapper: dict[Union[Type[DistributionLoad], Type[DistributionSolar]], Callable] = {
        DistributionLoad: get_aggregated_load_timeseries,
        DistributionSolar: get_aggregated_solar_timeseries,
        DistributionBattery: get_aggregated_battery_timeseries,
    }
    for node in reduced_network_tree.nodes():
        if reduced_network_tree.out_degree(node) < original_tree.out_degree(node):
            sucessors_diff = set(original_tree.successors(node)) - set(
                reduced_network_tree.successors(node)
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
                    reduced_system.get_component(DistributionBus, node),
                    model_type=model_type,
                    split_phase_mapping=split_phase_mapping,
                )
                # print(model_type.__name__, agg_component)
                reduced_system.add_component(agg_component)
                agg_comp = reduced_system.get_component(model_type, agg_component.name)
                if agg_timeseries:
                    comps = list(subtree_system.get_components(model_type))
                    ts_metadata = dist_system.list_time_series_metadata(
                        comps[0], time_series_type=time_series_type
                    )
                    for metadata in ts_metadata:
                        ts_aggregate = ts_agg_func_mapper[model_type](
                            dist_system, comps, metadata.variable_name, time_series_type
                        )
                        user_attr = UserAttributes.model_validate(metadata.user_attributes)
                        user_attr.use_actual = True
                        reduced_system.add_time_series(
                            ts_aggregate, agg_comp, **user_attr.model_dump()
                        )
    return reduced_system


def reduce_to_three_phase_system(
    dist_system: DistributionSystem,
    name: str,
    agg_timeseries: bool = False,
    time_series_type: Type[TimeSeriesData] = SingleTimeSeries,
) -> DistributionSystem:
    three_phase_buses = get_three_phase_buses(dist_system)
    return _reduce_system(dist_system, three_phase_buses, name, agg_timeseries, time_series_type)


def reduce_to_primary_system(
    dist_system: DistributionSystem,
    name: str,
    agg_timeseries: bool = False,
    time_series_type: Type[TimeSeriesData] = SingleTimeSeries,
) -> DistributionSystem:
    primary_buses = get_primary_buses(dist_system)
    return _reduce_system(dist_system, primary_buses, name, agg_timeseries, time_series_type)
