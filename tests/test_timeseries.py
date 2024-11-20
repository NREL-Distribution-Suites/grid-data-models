from pathlib import Path

import pandas as pd
import numpy as np

from gdm.distribution.components.distribution_capacitor import DistributionCapacitor
from gdm.distribution.distribution_system import DistributionSystem
from gdm.distribution.sys_functools import (
    get_combined_load_timeseries_df,
    get_combined_solar_timeseries_df,
)


def test_combined_timeseries_on_smartds():
    data_path = Path(__file__).parent / "data/p5r_pv.json"
    gdm_sys: DistributionSystem = DistributionSystem.from_json(data_path)
    load_df = get_combined_load_timeseries_df(
        gdm_sys, {"active_power": "kilowatts", "reactive_power": "kilovar"}
    )
    solar_df = get_combined_solar_timeseries_df(gdm_sys, {"irradiance": "kilowatts"})
    assert isinstance(load_df, pd.DataFrame)
    assert isinstance(solar_df, pd.DataFrame)
    total_capacitors = sum(
        [
            ph_cap.rated_capacity
            for cap in gdm_sys.get_components(DistributionCapacitor)
            for ph_cap in cap.equipment.phase_capacitors
        ]
    )
    load_time_series = load_df.groupby(["variable_name", "timestamp"], as_index=False).sum(
        ["value"]
    )
    load_df_pivoted = load_time_series.pivot(
        index="timestamp", columns="variable_name", values="value"
    )
    solar_time_series = solar_df.groupby(["variable_name", "timestamp"], as_index=False).sum(
        ["value"]
    )
    solar_df_pivoted = solar_time_series.pivot(
        index="timestamp", columns="variable_name", values="value"
    )
    merged_dataframe = load_df_pivoted.merge(solar_df_pivoted, left_index=True, right_index=True)
    merged_dataframe["kva"] = np.sqrt(
        (merged_dataframe["active_power"] - merged_dataframe["irradiance"]) ** 2
        + (merged_dataframe["reactive_power"] - total_capacitors.to("kilovar").magnitude) ** 2
    )
    merged_dataframe = merged_dataframe.sort_index()
    opendss_ckt_power = pd.read_csv(Path(__file__).parent / "data/ckt_power_p5r.csv")
    opendss_ckt_power["opendss_kva"] = (
        opendss_ckt_power[" S1 (kVA)"]
        + opendss_ckt_power[" S2 (kVA)"]
        + opendss_ckt_power[" S3 (kVA)"]
    )
    opendss_ckt_power["opendss_active_power"] = (
        opendss_ckt_power[" S1 (kVA)"] * np.cos(np.deg2rad(opendss_ckt_power[" Ang1"]))
        + opendss_ckt_power[" S2 (kVA)"] * np.cos(np.deg2rad(opendss_ckt_power[" Ang2"]))
        + opendss_ckt_power[" S3 (kVA)"] * np.cos(np.deg2rad(opendss_ckt_power[" Ang3"]))
    )
    opendss_ckt_power["opendss_reactive_power"] = (
        opendss_ckt_power[" S1 (kVA)"] * np.sin(np.deg2rad(opendss_ckt_power[" Ang1"]))
        + opendss_ckt_power[" S2 (kVA)"] * np.sin(np.deg2rad(opendss_ckt_power[" Ang2"]))
        + opendss_ckt_power[" S3 (kVA)"] * np.sin(np.deg2rad(opendss_ckt_power[" Ang3"]))
    )
    opendss_result = opendss_ckt_power[
        ["opendss_kva", "opendss_active_power", "opendss_reactive_power"]
    ]
    opendss_result.index = merged_dataframe.index
    merged_dataframe = merged_dataframe.merge(opendss_result, left_index=True, right_index=True)
