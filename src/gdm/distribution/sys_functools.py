import pandas as pd

from infrasys.time_series_models import SingleTimeSeries, SingleTimeSeriesMetadata
from infrasys.normalization import NormalizationMax, NormalizationByValue
from pint import Quantity
from numpy.typing import NDArray
import numpy as np

from gdm.distribution.components.distribution_load import DistributionLoad
from gdm.distribution.components.distribution_solar import DistributionSolar
from gdm.distribution.distribution_system import DistributionSystem, UserAttributes
from gdm.exceptions import (
    InconsistentTimeseriesAggregation,
    NoComponentsFoundError,
    NoTimeSeriesDataFound,
    TimeseriesVariableDoesNotExist,
    UnsupportedVariableError,
)
from gdm.quantities import PositiveActivePower


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
            return denormalized_data.magnitude * sum(
                [ph_load.real_power for ph_load in load.equipment.phase_loads]
            )
        case "reactive_power":
            return denormalized_data.magnitude * sum(
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


def get_aggregated_solar_timeseries(
    sys: DistributionSystem, solars: list[DistributionSolar], var_name: str
) -> SingleTimeSeries:
    """Method to return combined solar time series data.

    Parameters
    ----------
    sys: DistributionSystem
        Instance of the DistributionSystem
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
        sys.get_time_series(solar, var_name) for solar in solars
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


def get_aggregated_load_timeseries(
    sys: DistributionSystem, loads: list[DistributionLoad], var_name: str
) -> SingleTimeSeries:
    """Method to return combined load time series data.

    Parameters
    ----------
    sys: DistributionSystem
        Instance of the DistributionSystem
    loads: list[DistributionLoad]
        List of loads for aggregating timeseries data.
    var_name: str
        Variable name used for time series aggregation.

    Returns
    -------
    SingleTimeSeries
    """
    ts_components: list[SingleTimeSeries] = [sys.get_time_series(load, var_name) for load in loads]
    _check_for_timeseries_consistency(ts_components)
    ts_metadata = list[SingleTimeSeriesMetadata] = [
        sys.list_time_series_metadata(load, var_name)[0] for load in loads
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


def _get_combined_timeseries_df(
    sys: DistributionSystem,
    component_type: type,
    var_of_interest: set[str],
    power_function: callable,
    unit_conversion: dict[str, str],
) -> pd.DataFrame:
    """
    Generalized function for returning combined timeseries dataframe for given component type.

    Parameters
    ----------
    sys: DistributionSystem
        Instance of DistributionSystem.
    component_type: type
        The type of components to retrieve (e.g., DistributionLoad, DistributionSolar).
    var_of_interest: set[str]
        Set of variable names of interest.
    power_function: callable
        Function to compute power data for the component.
    unit_conversion: dict[str, str]
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
    components = list(sys.get_components(component_type))
    if not components:
        raise NoComponentsFoundError(
            f"No components of type {component_type.__name__} found in {sys.name}"
        )

    for component in components:
        ts_metadata = sys.list_time_series_metadata(component)
        if not ts_metadata:
            msg = f"No timeseries data found for {component=}."
            raise NoTimeSeriesDataFound(msg)
        avail_vars = {md.variable_name for md in ts_metadata}

        if not var_of_interest.issubset(avail_vars):
            msg = f"{avail_vars=}. Only {var_of_interest=} is supported for dataframe computation."
            raise TimeseriesVariableDoesNotExist(msg)

        for var in var_of_interest & avail_vars:
            ts_data: SingleTimeSeries = sys.get_time_series(component, variable_name=var)
            metadata = [meta for meta in ts_metadata if meta.variable_name == var][0]
            power_data = power_function(component, ts_data, metadata)
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
                            unit_conversion[var] if var in unit_conversion else power_data.units
                        ]
                        * ts_data.length,
                    }
                )
            )

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def get_combined_load_timeseries_df(
    sys: DistributionSystem, unit_conversion: dict[str, str]
) -> pd.DataFrame:
    """
    Function for returning combined timeseries dataframe for load components.

    Parameters
    ----------
    sys: DistributionSystem
        Instance of DistributionSystem.
    unit_conversion: dict[str, str]
        Optional dictionary to perform unit conversion on data in pint quantities.

    Returns
    -------
    pd.DataFrame
    """
    return _get_combined_timeseries_df(
        sys=sys,
        component_type=DistributionLoad,
        var_of_interest={"active_power", "reactive_power"},
        power_function=_get_load_power,
        unit_conversion=unit_conversion,
    )


def get_combined_solar_timeseries_df(
    sys: DistributionSystem, unit_conversion: dict[str, str]
) -> pd.DataFrame:
    """
    Function for returning combined timeseries dataframe for solar components.

    Parameters
    ----------
    sys: DistributionSystem
        Instance of DistributionSystem.
    unit_conversion: dict[str, str]
        Optional dictionary to perform unit conversion on data in pint quantities.

    Returns
    -------
    pd.DataFrame
    """
    solar_df = _get_combined_timeseries_df(
        sys=sys,
        component_type=DistributionSolar,
        var_of_interest={"irradiance"},
        power_function=_get_solar_power,
        unit_conversion=unit_conversion,
    )
    return solar_df.rename(columns={"irradiance": "active_power"})
