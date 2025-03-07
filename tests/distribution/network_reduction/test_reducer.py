from infrasys.time_series_models import SingleTimeSeries, NonSequentialTimeSeries

from gdm.distribution.network.reducer import reduce_to_three_phase_system
from gdm import DistributionSystem, DistributionLoad, DistributionBus


def get_total_kw(load: DistributionLoad):
    return sum([item.real_power.to("megawatt").magnitude for item in load.equipment.phase_loads])


def get_total_kvar(load: DistributionLoad):
    return sum(
        [item.reactive_power.to("megavar").magnitude for item in load.equipment.phase_loads]
    )


def test_three_phase_network_reducer_with_single_timeseries(
    distribution_system_with_single_timeseries,
):
    gdm_sys: DistributionSystem = distribution_system_with_single_timeseries
    reduce_to_three_phase_system(
        gdm_sys, name="reduced_system", agg_timeseries=True, time_series_type=SingleTimeSeries
    )


def test_three_phase_network_reducer_with_nonsequential_timeseries(
    distribution_system_with_nonsequential_timeseries,
):
    gdm_sys: DistributionSystem = distribution_system_with_nonsequential_timeseries
    reduce_to_three_phase_system(
        gdm_sys,
        name="reduced_system",
        agg_timeseries=True,
        time_series_type=NonSequentialTimeSeries,
    )


def test_three_phase_network_reducer(distribution_system_with_single_timeseries):
    gdm_sys: DistributionSystem = distribution_system_with_single_timeseries
    reducer = reduce_to_three_phase_system(gdm_sys, name="reduced_system", agg_timeseries=False)
    bus = list(reducer.get_components(DistributionBus))[0]

    split_phase_mapping = gdm_sys.get_split_phase_mapping()
    reducer_total_load = DistributionLoad.aggregate(
        list(reducer.get_components(DistributionLoad)),
        bus,
        "reducer_total",
        split_phase_mapping,
    )
    gdm_total_load = DistributionLoad.aggregate(
        list(gdm_sys.get_components(DistributionLoad)),
        bus,
        "gdm_total",
        split_phase_mapping,
    )
    assert get_total_kw(reducer_total_load) == get_total_kw(gdm_total_load), f"""Active power Reduced: {get_total_kw(reducer_total_load)} MW,
        Original: {get_total_kw(gdm_total_load)} MW"""

    assert get_total_kvar(reducer_total_load) == get_total_kvar(gdm_total_load), f"""Reactive power Reduced: {get_total_kvar(reducer_total_load)} Mvar,
        Original: {get_total_kvar(gdm_total_load)} Mvar"""
