import pandas as pd
import numpy as np
from gdm.distribution.distribution_system import DistributionSystem
from gdm.distribution.sys_functools import (
    get_combined_load_timeseries_df,
    get_combined_solar_timeseries_df,
)
from gdm import DistributionLoad, DistributionSolar


def process_timeseries(df: pd.DataFrame, value_column: str) -> pd.DataFrame:
    """Aggregate and pivot the time series DataFrame."""
    grouped_df = df.groupby(["variable_name", "timestamp"], as_index=False).sum([value_column])
    pivoted_df = grouped_df.pivot(index="timestamp", columns="variable_name", values=value_column)
    return pivoted_df


def test_combined_timeseries_on_smartds(sample_distribution_system_with_timeseries):
    """Test the integration of load and solar time series with OpenDSS results."""

    gdm_sys: DistributionSystem = sample_distribution_system_with_timeseries

    # Process load and solar time series
    load_df = process_timeseries(
        get_combined_load_timeseries_df(
            gdm_sys, {"active_power": "kilowatts", "reactive_power": "kilovar"}
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

    solar_df = process_timeseries(
        get_combined_solar_timeseries_df(gdm_sys, {"irradiance": "kilowatts"}),
        value_column="value",
    )
    solar_df = solar_df.rename(columns={"active_power": "solar_active_power"})

    pvs: list[DistributionSolar] = list(gdm_sys.get_components(DistributionSolar))
    pv_powers_dc = [pv.equipment.solar_power.to("kilowatts").magnitude for pv in pvs]
    assert np.array_equal(
        solar_df["solar_active_power"].values, np.array([0, 0.5, 1, 0.5, 0]) * sum(pv_powers_dc)
    )
