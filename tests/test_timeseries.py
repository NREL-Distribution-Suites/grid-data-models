from pathlib import Path
import pandas as pd
import numpy as np
from gdm.distribution.distribution_system import DistributionSystem
from gdm.distribution.sys_functools import (
    get_combined_load_timeseries_df,
    get_combined_solar_timeseries_df,
)


def load_distribution_system(data_path: Path) -> DistributionSystem:
    """Load the distribution system from a JSON file."""
    return DistributionSystem.from_json(data_path)


def process_timeseries(df: pd.DataFrame, value_column: str) -> pd.DataFrame:
    """Aggregate and pivot the time series DataFrame."""
    grouped_df = df.groupby(["variable_name", "timestamp"], as_index=False).sum([value_column])
    pivoted_df = grouped_df.pivot(index="timestamp", columns="variable_name", values=value_column)
    return pivoted_df


def calculate_kva(merged_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the apparent power (kVA) and update the DataFrame."""
    merged_df["kva"] = np.sqrt(
        (merged_df["active_power"] - merged_df["solar_active_power"]) ** 2
        + merged_df["reactive_power"] ** 2
    )
    return merged_df.sort_index()


def process_opendss_results(opendss_path: Path) -> pd.DataFrame:
    """Process OpenDSS simulation results and calculate derived columns."""
    opendss_ckt_power = pd.read_csv(opendss_path)
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
    return opendss_ckt_power[["opendss_kva", "opendss_active_power", "opendss_reactive_power"]]


def merge_results(
    load_df: pd.DataFrame,
    solar_df: pd.DataFrame,
    opendss_results: pd.DataFrame,
) -> pd.DataFrame:
    """Merge load, solar, and OpenDSS results into a single DataFrame."""
    merged_df = load_df.merge(solar_df, left_index=True, right_index=True)
    merged_df = calculate_kva(merged_df)
    opendss_results.index = merged_df.index
    return merged_df.merge(opendss_results, left_index=True, right_index=True)


def validate_results(merged_df: pd.DataFrame):
    """Validate the results by comparing calculated and OpenDSS values."""
    error = list(
        (merged_df["opendss_active_power"] - merged_df["active_power"])
        * 100
        / merged_df["opendss_active_power"]
    )
    assert max(error) < 17, f"Maximum error exceeded: {max(error)}%"


def test_combined_timeseries_on_smartds():
    """Test the integration of load and solar time series with OpenDSS results."""
    # Load data
    data_path = Path(__file__).parent / "data/p5r_pv.json"
    opendss_path = Path(__file__).parent / "data/ckt_power_p5r_no_cap.csv"

    gdm_sys = load_distribution_system(data_path)

    # Process load and solar time series
    load_df = process_timeseries(
        get_combined_load_timeseries_df(
            gdm_sys, {"active_power": "kilowatts", "reactive_power": "kilovar"}
        ),
        value_column="value",
    )
    solar_df = process_timeseries(
        get_combined_solar_timeseries_df(gdm_sys, {"irradiance": "kilowatts"}),
        value_column="value",
    )
    solar_df = solar_df.rename(columns={"active_power": "solar_active_power"})

    # Process OpenDSS results
    opendss_results = process_opendss_results(opendss_path)

    # Merge results and validate
    merged_df = merge_results(load_df, solar_df, opendss_results)
    validate_results(merged_df)
