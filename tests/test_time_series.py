from datetime import datetime, timedelta

import pytest
import pandas as pd
import numpy as np

from infrasys import NonSequentialTimeSeries, SingleTimeSeries

from gdm.distribution.distribution_system import DistributionSystem
from gdm.distribution.components import DistributionLoad, DistributionSolar
from gdm.distribution.sys_functools import (
    get_combined_solar_time_series_df,
    get_combined_load_time_series_df,
)
from gdm.exceptions import (
    IncompatibleTimeSeries,
    NoComponentsFoundError,
    NoTimeSeriesDataFound,
    TimeSeriesVariableDoesNotExist,
    GDMQuantityError,
    GDMQuantityUnitsError,
)

from gdm.quantities import ActivePower


class CustomTimeSeries:
    "A dummy time series class for test"


def process_time_series(df: pd.DataFrame, value_column: str) -> pd.DataFrame:
    """Aggregate and pivot the time series DataFrame."""
    grouped_df = df.groupby(["variable_name", "timestamp"], as_index=False).sum([value_column])
    pivoted_df = grouped_df.pivot(index="timestamp", columns="variable_name", values=value_column)
    return pivoted_df


def test_combined_single_time_series_on_smartds(distribution_system_with_single_time_series):
    """Test the integration of load and solar time series with OpenDSS results."""

    gdm_sys: DistributionSystem = distribution_system_with_single_time_series

    # Process load and solar time series
    load_df = process_time_series(
        get_combined_load_time_series_df(
            gdm_sys,
            {"active_power": "kilowatts", "reactive_power": "kilovar"},
            time_series_type=SingleTimeSeries,
        ),
        value_column="value",
    )

    loads: list[DistributionLoad] = list(gdm_sys.get_components(DistributionLoad))
    load_q = [
        phsload.reactive_power.to("kilovar").magnitude
        for load in loads
        for phsload in load.equipment.phase_loads
    ]
    total_reactive_power = [sum(load_q) * (i + 1) for i in range(5)]
    num_loads = len(loads)

    assert np.array_equal(load_df["active_power"].values, np.array([1, 2, 3, 4, 5]) * num_loads)
    assert np.array_equal(load_df["reactive_power"].values, np.array(total_reactive_power))

    solar_df = process_time_series(
        get_combined_solar_time_series_df(
            gdm_sys, {"irradiance": "kilowatts"}, time_series_type=SingleTimeSeries
        ),
        value_column="value",
    )
    solar_df = solar_df.rename(columns={"active_power": "solar_active_power"})

    pvs: list[DistributionSolar] = list(gdm_sys.get_components(DistributionSolar))
    pv_powers_dc = [pv.active_power.to("kilowatts").magnitude for pv in pvs]
    assert np.array_equal(
        solar_df["solar_active_power"].values, np.array([0, 0.5, 1, 0.5, 0]) * sum(pv_powers_dc)
    )


def test_combined_nonsequential_time_series_on_smartds(
    distribution_system_with_nonsequential_time_series,
):
    """Test the integration of load and solar time series with OpenDSS results."""

    gdm_sys: DistributionSystem = distribution_system_with_nonsequential_time_series

    # Process load and solar time series
    load_df = process_time_series(
        get_combined_load_time_series_df(
            gdm_sys,
            {"active_power": "kilowatts", "reactive_power": "kilovar"},
            time_series_type=NonSequentialTimeSeries,
        ),
        value_column="value",
    )

    loads: list[DistributionLoad] = list(gdm_sys.get_components(DistributionLoad))
    load_q = [
        phsload.reactive_power.to("kilovar").magnitude
        for load in loads
        for phsload in load.equipment.phase_loads
    ]
    total_reactive_power = [sum(load_q) * (i + 1) for i in range(5)]
    num_loads = len(loads)

    assert np.array_equal(load_df["active_power"].values, np.array([1, 2, 3, 4, 5]) * num_loads)
    assert np.array_equal(load_df["reactive_power"].values, np.array(total_reactive_power))

    solar_df = process_time_series(
        get_combined_solar_time_series_df(
            gdm_sys, {"irradiance": "kilowatts"}, time_series_type=NonSequentialTimeSeries
        ),
        value_column="value",
    )
    solar_df = solar_df.rename(columns={"active_power": "solar_active_power"})

    pvs: list[DistributionSolar] = list(gdm_sys.get_components(DistributionSolar))
    pv_powers_dc = [pv.active_power.to("kilowatts").magnitude for pv in pvs]
    assert np.array_equal(
        solar_df["solar_active_power"].values, np.array([0, 0.5, 1, 0.5, 0]) * sum(pv_powers_dc)
    )


def test_incompatible_time_series_error(distribution_system_with_nonsequential_time_series):
    """Test to raise error when incompatible time series is passed"""
    gdm_sys = distribution_system_with_nonsequential_time_series

    with pytest.raises(IncompatibleTimeSeries):
        get_combined_load_time_series_df(
            gdm_sys,
            {"active_power": "kilowatts", "reactive_power": "kilovar"},
            time_series_type=CustomTimeSeries,
        )

    with pytest.raises(IncompatibleTimeSeries):
        get_combined_solar_time_series_df(
            gdm_sys,
            {"irradiance": "kilowatts"},
            time_series_type=CustomTimeSeries,
        )


def test_nocomponents_error_nonsequential_time_series(
    distribution_system_with_nonsequential_time_series,
):
    """Test to raise error when components are not found"""
    gdm_sys = distribution_system_with_nonsequential_time_series

    loads = list(gdm_sys.get_components(DistributionLoad))
    solars = list(gdm_sys.get_components(DistributionSolar))
    for each_load in loads:
        gdm_sys.remove_component(each_load)

    for each_solar in solars:
        gdm_sys.remove_component(each_solar)

    with pytest.raises(NoComponentsFoundError):
        get_combined_load_time_series_df(
            gdm_sys,
            {"active_power": "kilowatts", "reactive_power": "kilovar"},
            time_series_type=NonSequentialTimeSeries,
        )

    with pytest.raises(NoComponentsFoundError):
        get_combined_solar_time_series_df(
            gdm_sys,
            {"irradiance": "kilowatts"},
            time_series_type=NonSequentialTimeSeries,
        )


def test_nocomponents_error_single_time_series(
    distribution_system_with_single_time_series,
):
    """Test to raise error when components are not found"""
    gdm_sys = distribution_system_with_single_time_series

    loads = list(gdm_sys.get_components(DistributionLoad))
    solars = list(gdm_sys.get_components(DistributionSolar))
    for each_load in loads:
        gdm_sys.remove_component(each_load)

    for each_solar in solars:
        gdm_sys.remove_component(each_solar)

    with pytest.raises(NoComponentsFoundError):
        get_combined_load_time_series_df(
            gdm_sys,
            {"active_power": "kilowatts", "reactive_power": "kilovar"},
            time_series_type=SingleTimeSeries,
        )

    with pytest.raises(NoComponentsFoundError):
        get_combined_solar_time_series_df(
            gdm_sys,
            {"irradiance": "kilowatts"},
            time_series_type=SingleTimeSeries,
        )


def test_time_series_data_error_nonsequential(distribution_system_with_nonsequential_time_series):
    """Test to raise error when time series data is missing"""
    gdm_sys = distribution_system_with_nonsequential_time_series

    with pytest.raises(NoTimeSeriesDataFound):
        get_combined_load_time_series_df(
            gdm_sys,
            {"active_power": "kilowatts", "reactive_power": "kilovar"},
            # SingleTimeSeries for NonSequentialTimeSeries gives empty metadata
            time_series_type=SingleTimeSeries,
        )

    with pytest.raises(NoTimeSeriesDataFound):
        get_combined_solar_time_series_df(
            gdm_sys,
            {"irradiance": "kilowatts"},
            time_series_type=SingleTimeSeries,
        )


def test_time_series_data_error_single_time_series(distribution_system_with_single_time_series):
    gdm_sys2 = distribution_system_with_single_time_series
    with pytest.raises(NoTimeSeriesDataFound):
        get_combined_load_time_series_df(
            gdm_sys2,
            {"active_power": "kilowatts", "reactive_power": "kilovar"},
            # SingleTimeSeries for NonSequentialTimeSeries gives empty metadata
            time_series_type=NonSequentialTimeSeries,
        )

    with pytest.raises(NoTimeSeriesDataFound):
        get_combined_solar_time_series_df(
            gdm_sys2,
            {"irradiance": "kilowatts"},
            time_series_type=NonSequentialTimeSeries,
        )


def test_time_series_variable_error_nonsequential_time_series(
    distribution_system_with_nonsequential_time_series,
):
    """Test to raise error when variable of interest does not exist"""
    gdm_sys = distribution_system_with_nonsequential_time_series
    with pytest.raises(TimeSeriesVariableDoesNotExist):
        get_combined_load_time_series_df(
            gdm_sys,
            {"active_power": "kilowatts", "reactive_power": "kilovar"},
            var_of_interest={"active_load"},
            time_series_type=NonSequentialTimeSeries,
        )

    with pytest.raises(TimeSeriesVariableDoesNotExist):
        get_combined_solar_time_series_df(
            gdm_sys,
            {"irradiance": "kilowatts"},
            var_of_interest={"active_solar"},
            time_series_type=NonSequentialTimeSeries,
        )


def test_time_series_variable_error_single_time_series(
    distribution_system_with_single_time_series,
):
    """Test to raise error when variable of interest does not exist"""
    gdm_sys = distribution_system_with_single_time_series

    with pytest.raises(TimeSeriesVariableDoesNotExist):
        get_combined_load_time_series_df(
            gdm_sys,
            {"active_power": "kilowatts", "reactive_power": "kilovar"},
            var_of_interest={"active_load"},
            time_series_type=SingleTimeSeries,
        )

    with pytest.raises(TimeSeriesVariableDoesNotExist):
        get_combined_solar_time_series_df(
            gdm_sys,
            {"irradiance": "kilowatts"},
            var_of_interest={"active_solar"},
            time_series_type=SingleTimeSeries,
        )


def test_quantity_error(simple_distribution_system):
    gdm_sys = simple_distribution_system
    load_profile_kw = SingleTimeSeries.from_array(
        data=[1, 2, 3, 4, 5],
        variable_name="active_power",
        initial_time=datetime(2020, 1, 1),
        resolution=timedelta(minutes=30),
    )
    loads = list(gdm_sys.get_components(DistributionLoad))
    gdm_sys.add_time_series(
        load_profile_kw,
        *loads,
        profile_type="PMult",
        profile_name="load_profile_kw",
        use_actual=True,
    )

    irradiance_profile = SingleTimeSeries.from_array(
        data=[1, 2, 3, 4, 5],
        variable_name="irradiance",
        initial_time=datetime(2020, 1, 1),
        resolution=timedelta(minutes=30),
    )
    pvs: list[DistributionSolar] = list(gdm_sys.get_components(DistributionSolar))
    gdm_sys.add_time_series(
        irradiance_profile,
        *pvs,
        profile_type="PMult",
        profile_name="pv_profile",
        use_actual=False,
    )
    with pytest.raises(GDMQuantityError):
        get_combined_load_time_series_df(
            gdm_sys,
            {"active_power": "kilowatts", "reactive_power": "kilovar"},
            var_of_interest={"active_power"},
            time_series_type=SingleTimeSeries,
        )

    with pytest.raises(GDMQuantityError):
        get_combined_solar_time_series_df(
            gdm_sys,
            {"active_power": "kilowatts", "reactive_power": "kilovar"},
            var_of_interest={"irradiance"},
            time_series_type=SingleTimeSeries,
        )

    gdm_sys2 = simple_distribution_system
    irradiance_profile = SingleTimeSeries.from_array(
        data=ActivePower([1, 2, 3, 4, 5], "kilovar"),
        variable_name="active_power",
        initial_time=datetime(2020, 1, 1),
        resolution=timedelta(minutes=30),
    )
    pvs: list[DistributionSolar] = list(gdm_sys2.get_components(DistributionSolar))
    gdm_sys2.add_time_series(
        irradiance_profile,
        *pvs,
        profile_type="PMult",
        profile_name="pv_profile",
        use_actual=True,
    )
    with pytest.raises(GDMQuantityUnitsError):
        get_combined_solar_time_series_df(
            gdm_sys2,
            {"active_power": "kilowatts", "reactive_power": "kilovar"},
            var_of_interest={"active_power"},
            time_series_type=SingleTimeSeries,
        )
