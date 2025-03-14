from datetime import timedelta, datetime
import pytest

from infrasys.time_series_models import SingleTimeSeries, NonSequentialTimeSeries

from gdm.distribution.network.reducer import reduce_to_three_phase_system, reduce_to_primary_system
from gdm.distribution.sys_functools import (
    get_aggregated_load_timeseries,
    get_aggregated_solar_timeseries,
)
from gdm import DistributionSystem, DistributionLoad, DistributionBus, DistributionSolar

from gdm.exceptions import (
    IncompatibleTimeSeries,
    UnsupportedVariableError,
    InconsistentTimeseriesAggregation,
)
from gdm.quantities import ActivePower, Irradiance


class CustomTimeSeries:
    "A dummy time series class for test"


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


def test_incompatible_timeseries_and_unsupported_variable_error(
    distribution_system_with_nonsequential_timeseries,
):
    """Test to raise error when incompatible timeseries is passed"""
    gdm_sys = distribution_system_with_nonsequential_timeseries
    loads = list(gdm_sys.get_components(DistributionLoad))
    solars = list(gdm_sys.get_components(DistributionSolar))

    with pytest.raises(IncompatibleTimeSeries):
        get_aggregated_load_timeseries(
            gdm_sys,
            loads,
            "active_power",
            time_series_type=CustomTimeSeries,
        )

    with pytest.raises(IncompatibleTimeSeries):
        get_aggregated_solar_timeseries(
            gdm_sys,
            solars,
            "irradiance",
            time_series_type=CustomTimeSeries,
        )

    with pytest.raises(UnsupportedVariableError):
        get_aggregated_solar_timeseries(
            gdm_sys,
            solars,
            "active_solar",
            time_series_type=SingleTimeSeries,
        )


def test_time_series_consistencies(simple_distribution_system):
    gdm_sys = simple_distribution_system
    load_profile_kw_1 = SingleTimeSeries.from_array(
        data=ActivePower([1, 2, 3, 4, 5], "kilowatt"),
        variable_name="active_power",
        initial_time=datetime(2020, 1, 1),
        resolution=timedelta(minutes=30),
    )
    load_profile_kw_2 = SingleTimeSeries.from_array(
        data=ActivePower([1, 2, 3, 4, 5, 6], "kilowatt"),
        variable_name="active_power",
        initial_time=datetime(2020, 1, 1),
        resolution=timedelta(minutes=30),
    )
    loads = list(gdm_sys.get_components(DistributionLoad))
    gdm_sys.add_time_series(
        load_profile_kw_2,
        loads[0],
        profile_type="PMult",
        profile_name="load_profile_kw",
        use_actual=True,
    )
    gdm_sys.add_time_series(
        load_profile_kw_1,
        *loads[1:],
        profile_type="PMult",
        profile_name="load_profile_kw",
        use_actual=True,
    )

    irradiance_profile_1 = SingleTimeSeries.from_array(
        data=Irradiance([0, 0.5, 1, 0.5, 0], "kilowatt / meter ** 2"),
        variable_name="irradiance",
        initial_time=datetime(2020, 1, 1),
        resolution=timedelta(minutes=30),
    )
    irradiance_profile_2 = SingleTimeSeries.from_array(
        data=Irradiance([0, 0.5, 0.8, 1, 0.5, 0], "kilowatt / meter ** 2"),
        variable_name="irradiance",
        initial_time=datetime(2020, 1, 1),
        resolution=timedelta(minutes=30),
    )
    pvs: list[DistributionSolar] = list(gdm_sys.get_components(DistributionSolar))
    gdm_sys.add_time_series(
        irradiance_profile_2,
        pvs[0],
        profile_type="PMult",
        profile_name="pv_profile",
        use_actual=False,
    )
    gdm_sys.add_time_series(
        irradiance_profile_1,
        *pvs[1:],
        profile_type="PMult",
        profile_name="pv_profile",
        use_actual=False,
    )
    with pytest.raises(InconsistentTimeseriesAggregation):
        get_aggregated_load_timeseries(
            gdm_sys,
            loads,
            "active_power",
            time_series_type=SingleTimeSeries,
        )
    with pytest.raises(InconsistentTimeseriesAggregation):
        get_aggregated_solar_timeseries(
            gdm_sys,
            pvs,
            "irradiance",
            time_series_type=SingleTimeSeries,
        )


def test_time_series_metadata_consistencies(simple_distribution_system):
    gdm_sys = simple_distribution_system
    load_profile_kw = SingleTimeSeries.from_array(
        data=ActivePower([1, 2, 3, 4, 5], "kilowatt"),
        variable_name="active_power",
        initial_time=datetime(2020, 1, 1),
        resolution=timedelta(minutes=30),
    )
    loads = list(gdm_sys.get_components(DistributionLoad))
    gdm_sys.add_time_series(
        load_profile_kw,
        loads[0],
        profile_type="PMult",
        profile_name="load_profile_kw",
        use_actual=True,
    )
    gdm_sys.add_time_series(
        load_profile_kw,
        *loads[1:],
        profile_type="PMult1",
        profile_name="load_profile_kw1",
        use_actual=True,
    )
    with pytest.raises(InconsistentTimeseriesAggregation):
        get_aggregated_load_timeseries(
            gdm_sys,
            loads,
            "active_power",
            time_series_type=SingleTimeSeries,
        )

    gdm_sys2 = simple_distribution_system
    load_profile_kw1 = NonSequentialTimeSeries.from_array(
        data=ActivePower([1, 2, 3, 4, 5], "kilowatt"),
        timestamps=[
            datetime(2020, 1, 1),
            datetime(2020, 1, 3),
            datetime(2020, 2, 1),
            datetime(2020, 2, 3),
            datetime(2020, 3, 1),
        ],
        variable_name="active_power",
    )
    load_profile_kw2 = NonSequentialTimeSeries.from_array(
        data=ActivePower([1, 2, 3, 4, 5, 6], "kilowatt"),
        timestamps=[
            datetime(2020, 1, 1),
            datetime(2020, 1, 3),
            datetime(2020, 2, 1),
            datetime(2020, 2, 3),
            datetime(2020, 3, 1),
            datetime(2020, 3, 2),
        ],
        variable_name="active_power",
    )
    loads = list(gdm_sys.get_components(DistributionLoad))
    gdm_sys2.add_time_series(
        load_profile_kw2,
        loads[0],
        profile_type="PMult",
        profile_name="load_profile_kw",
        use_actual=True,
    )
    gdm_sys2.add_time_series(
        load_profile_kw1,
        *loads[1:],
        profile_type="PMult1",
        profile_name="load_profile_kw1",
        use_actual=True,
    )
    with pytest.raises(InconsistentTimeseriesAggregation):
        get_aggregated_load_timeseries(
            gdm_sys2,
            loads,
            "active_power",
            time_series_type=NonSequentialTimeSeries,
        )


def test_time_series_unsupported_var(simple_distribution_system):
    gdm_sys = simple_distribution_system
    load_profile_kw = SingleTimeSeries.from_array(
        data=ActivePower([1, 2, 3, 4, 5], "kilowatt"),
        variable_name="active_load",
        initial_time=datetime(2020, 1, 1),
        resolution=timedelta(minutes=30),
    )
    loads = list(gdm_sys.get_components(DistributionLoad))
    gdm_sys.add_time_series(
        load_profile_kw,
        *loads,
        profile_type="PMult",
        profile_name="load_profile_kw",
        use_actual=False,
    )
    with pytest.raises(UnsupportedVariableError):
        get_aggregated_load_timeseries(
            gdm_sys,
            loads,
            "active_load",
            time_series_type=SingleTimeSeries,
        )


def test_reduce_to_primary_system(distribution_system_with_single_timeseries):
    gdm_sys: DistributionSystem = distribution_system_with_single_timeseries
    reducer = reduce_to_primary_system(gdm_sys, name="reduced_system", agg_timeseries=False)
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
