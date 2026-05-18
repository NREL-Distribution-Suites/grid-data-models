from datetime import datetime, timedelta

import pytest
import pandas as pd
import numpy as np

from infrasys import NonSequentialTimeSeries, SingleTimeSeries

from gdm.distribution.distribution_system import DistributionSystem
from gdm.distribution.components import DistributionLoad, DistributionSolar
from gdm.distribution.enums import Phase
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
    grouped_df = df.groupby(["name", "timestamp"], as_index=False)[[value_column]].sum()
    pivoted_df = grouped_df.pivot(index="timestamp", columns="name", values=value_column)
    return pivoted_df


def test_combined_single_timeseries_on_smartds(distribution_system_with_single_time_series):
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


def test_combined_nonsequential_timeseries_on_smartds(
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


def test_incompatible_timeseries_error(distribution_system_with_nonsequential_time_series):
    """Test to raise error when incompatible timeseries is passed"""
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
        name="active_power",
        initial_timestamp=datetime(2020, 1, 1),
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
        name="irradiance",
        initial_timestamp=datetime(2020, 1, 1),
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
        name="active_power",
        initial_timestamp=datetime(2020, 1, 1),
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


# ── aggregate_phases=True default ──────────────────────────────────────────


def test_aggregate_phases_default_no_phase_column(distribution_system_with_single_time_series):
    """Default behavior (aggregate_phases=True) must not emit a 'phase' column."""
    gdm_sys: DistributionSystem = distribution_system_with_single_time_series
    df = get_combined_load_time_series_df(
        gdm_sys,
        unit_conversion={"active_power": "kilowatts"},
        var_of_interest={"active_power"},
        time_series_type=SingleTimeSeries,
    )
    assert "phase" not in df.columns


# ── aggregate_phases=False (per-phase) ─────────────────────────────────────


def test_load_per_phase_single_time_series(distribution_system_with_single_time_series):
    """aggregate_phases=False emits a 'phase' column with per-phase power values."""
    gdm_sys: DistributionSystem = distribution_system_with_single_time_series

    df = get_combined_load_time_series_df(
        gdm_sys,
        unit_conversion={"reactive_power": "kilovar"},
        var_of_interest={"reactive_power"},
        aggregate_phases=False,
        time_series_type=SingleTimeSeries,
    )

    assert "phase" in df.columns

    loads: list[DistributionLoad] = list(gdm_sys.get_components(DistributionLoad))
    # Each load contributes len(phases) rows per timestamp
    expected_rows = sum(len(load.phases) for load in loads) * 5
    assert len(df) == expected_rows

    # For a 3-phase load, per-phase reactive value == multiplier × phase_peak
    # (NOT multiplier × sum_of_3_phase_peaks as the aggregated version would give)
    three_phase_load = next(
        load for load in loads if len(load.phases) == 3 and Phase.A in load.phases
    )
    phase_a_rows = df[
        (df["component_uuid"] == three_phase_load.uuid) & (df["phase"] == Phase.A)
    ].sort_values("timestamp")
    phase_peak_kvar = (
        three_phase_load.equipment.phase_loads[0].reactive_power.to("kilovar").magnitude
    )
    assert np.allclose(phase_a_rows["value"].values, np.array([1, 2, 3, 4, 5]) * phase_peak_kvar)


def test_load_per_phase_nonsequential_time_series(
    distribution_system_with_nonsequential_time_series,
):
    """aggregate_phases=False works for NonSequentialTimeSeries loads."""
    gdm_sys: DistributionSystem = distribution_system_with_nonsequential_time_series

    df = get_combined_load_time_series_df(
        gdm_sys,
        unit_conversion={"reactive_power": "kilovar"},
        var_of_interest={"reactive_power"},
        aggregate_phases=False,
        time_series_type=NonSequentialTimeSeries,
    )

    assert "phase" in df.columns

    loads: list[DistributionLoad] = list(gdm_sys.get_components(DistributionLoad))
    expected_rows = sum(len(load.phases) for load in loads) * 5
    assert len(df) == expected_rows

    three_phase_load = next(
        load for load in loads if len(load.phases) == 3 and Phase.A in load.phases
    )
    phase_a_rows = df[
        (df["component_uuid"] == three_phase_load.uuid) & (df["phase"] == Phase.A)
    ].sort_values("timestamp")
    phase_peak_kvar = (
        three_phase_load.equipment.phase_loads[0].reactive_power.to("kilovar").magnitude
    )
    assert np.allclose(phase_a_rows["value"].values, np.array([1, 2, 3, 4, 5]) * phase_peak_kvar)


def test_solar_per_phase_single_time_series(distribution_system_with_single_time_series):
    """aggregate_phases=False splits total solar power equally across phases."""
    gdm_sys: DistributionSystem = distribution_system_with_single_time_series

    per_phase_df = get_combined_solar_time_series_df(
        gdm_sys,
        unit_conversion={"irradiance": "kilowatts"},
        aggregate_phases=False,
        time_series_type=SingleTimeSeries,
    )
    assert "phase" in per_phase_df.columns

    pvs: list[DistributionSolar] = list(gdm_sys.get_components(DistributionSolar))
    expected_rows = sum(len(pv.phases) for pv in pvs) * 5
    assert len(per_phase_df) == expected_rows

    # Per-phase value == total / n_phases for each component
    agg_df = get_combined_solar_time_series_df(
        gdm_sys,
        unit_conversion={"irradiance": "kilowatts"},
        aggregate_phases=True,
        time_series_type=SingleTimeSeries,
    )
    for pv in pvs:
        n_phases = len(pv.phases)
        agg_vals = (
            agg_df[agg_df["component_uuid"] == pv.uuid].sort_values("timestamp")["value"].values
        )
        for phase in pv.phases:
            phase_vals = (
                per_phase_df[
                    (per_phase_df["component_uuid"] == pv.uuid) & (per_phase_df["phase"] == phase)
                ]
                .sort_values("timestamp")["value"]
                .values
            )
            assert np.allclose(phase_vals, agg_vals / n_phases)


def test_solar_per_phase_nonsequential_time_series(
    distribution_system_with_nonsequential_time_series,
):
    """aggregate_phases=False works for NonSequentialTimeSeries solar."""
    gdm_sys: DistributionSystem = distribution_system_with_nonsequential_time_series

    df = get_combined_solar_time_series_df(
        gdm_sys,
        unit_conversion={"irradiance": "kilowatts"},
        aggregate_phases=False,
        time_series_type=NonSequentialTimeSeries,
    )
    assert "phase" in df.columns

    pvs: list[DistributionSolar] = list(gdm_sys.get_components(DistributionSolar))
    expected_rows = sum(len(pv.phases) for pv in pvs) * 5
    assert len(df) == expected_rows


# ── include_features=True ──────────────────────────────────────────────────


def test_include_features_load_single_time_series(distribution_system_with_single_time_series):
    """include_features=True adds metadata.features columns (excluding use_actual)."""
    gdm_sys: DistributionSystem = distribution_system_with_single_time_series

    df = get_combined_load_time_series_df(
        gdm_sys,
        unit_conversion={"active_power": "kilowatts", "reactive_power": "kilovar"},
        include_features=True,
        time_series_type=SingleTimeSeries,
    )

    assert "profile_type" in df.columns
    assert "profile_name" in df.columns
    assert "use_actual" not in df.columns

    ap_rows = df[df["name"] == "active_power"]
    assert (ap_rows["profile_type"] == "PMult").all()
    assert (ap_rows["profile_name"] == "load_profile_kw").all()

    rp_rows = df[df["name"] == "reactive_power"]
    assert (rp_rows["profile_type"] == "QMult").all()
    assert (rp_rows["profile_name"] == "load_profile_kvar").all()


def test_include_features_load_nonsequential_time_series(
    distribution_system_with_nonsequential_time_series,
):
    """include_features=True works for NonSequentialTimeSeries loads."""
    gdm_sys: DistributionSystem = distribution_system_with_nonsequential_time_series

    df = get_combined_load_time_series_df(
        gdm_sys,
        unit_conversion={"active_power": "kilowatts", "reactive_power": "kilovar"},
        include_features=True,
        time_series_type=NonSequentialTimeSeries,
    )

    assert "profile_type" in df.columns
    assert "profile_name" in df.columns
    assert "use_actual" not in df.columns

    ap_rows = df[df["name"] == "active_power"]
    assert (ap_rows["profile_type"] == "PMult").all()
    assert (ap_rows["profile_name"] == "load_profile_kw").all()


def test_include_features_solar_single_time_series(distribution_system_with_single_time_series):
    """include_features=True adds features columns for solar."""
    gdm_sys: DistributionSystem = distribution_system_with_single_time_series

    df = get_combined_solar_time_series_df(
        gdm_sys,
        unit_conversion={"irradiance": "kilowatts"},
        include_features=True,
        time_series_type=SingleTimeSeries,
    )

    assert "profile_type" in df.columns
    assert "profile_name" in df.columns
    assert "use_actual" not in df.columns
    assert (df["profile_type"] == "PMult").all()
    assert (df["profile_name"] == "pv_profile").all()


def test_load_per_phase_and_features(distribution_system_with_single_time_series):
    """aggregate_phases=False and include_features=True work together."""
    gdm_sys: DistributionSystem = distribution_system_with_single_time_series

    df = get_combined_load_time_series_df(
        gdm_sys,
        unit_conversion={"reactive_power": "kilovar"},
        var_of_interest={"reactive_power"},
        aggregate_phases=False,
        include_features=True,
        time_series_type=SingleTimeSeries,
    )

    assert "phase" in df.columns
    assert "profile_type" in df.columns
    assert "profile_name" in df.columns
    assert "use_actual" not in df.columns


def test_include_features_arbitrary_string_feature(simple_distribution_system):
    """include_features=True includes arbitrary extra features like scenario='Scenario1'."""
    gdm_sys: DistributionSystem = simple_distribution_system

    load_profile_kw = SingleTimeSeries.from_array(
        data=ActivePower([1, 2, 3, 4, 5], "kilowatt"),
        name="active_power",
        initial_timestamp=datetime(2020, 1, 1),
        resolution=timedelta(minutes=30),
    )
    loads: list[DistributionLoad] = list(gdm_sys.get_components(DistributionLoad))
    gdm_sys.add_time_series(
        load_profile_kw,
        *loads,
        profile_type="PMult",
        profile_name="load_profile_kw",
        use_actual=True,
        scenario="Scenario1",
    )

    df = get_combined_load_time_series_df(
        gdm_sys,
        unit_conversion={"active_power": "kilowatts"},
        var_of_interest={"active_power"},
        include_features=True,
        time_series_type=SingleTimeSeries,
    )

    assert "scenario" in df.columns
    assert (df["scenario"] == "Scenario1").all()
    assert "use_actual" not in df.columns
