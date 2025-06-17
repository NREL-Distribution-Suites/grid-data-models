from typing import Type, Callable
from functools import singledispatch

import pandas as pd

from infrasys.time_series_models import (
    SingleTimeSeriesMetadata,
    NonSequentialTimeSeries,
    TimeSeriesMetadata,
    SingleTimeSeries,
    TimeSeriesData,
)
from infrasys.normalization import NormalizationMax, NormalizationByValue
from infrasys.component import Component
from pint import Quantity
import numpy as np

from gdm.distribution.components.distribution_load import DistributionLoad
from gdm.distribution.components.distribution_solar import DistributionSolar
from gdm.distribution.components.distribution_battery import DistributionBattery
from gdm.distribution.distribution_system import DistributionSystem, UserAttributes
from gdm.exceptions import (
    InconsistentTimeseriesAggregation,
    NoComponentsFoundError,
    NoTimeSeriesDataFound,
    TimeseriesVariableDoesNotExist,
    UnsupportedVariableError,
    IncompatibleTimeSeries,
    GDMQuantityError,
    GDMQuantityUnitsError,
)
from gdm.quantities import ActivePower


def get_timeseries_actual_data(
    ts_data: SingleTimeSeries | NonSequentialTimeSeries,
) -> Quantity:
    """Function to return denormalized load power, if normalized."""
    return _apply_normalization(ts_data.normalization, ts_data.data)


@singledispatch
def _apply_normalization(normalization, data):
    msg = f"Unspported type of normalization {type(normalization)=}"
    raise TypeError(msg)


@_apply_normalization.register
def _(normalization: None, data) -> Quantity:
    return data


@_apply_normalization.register(NormalizationMax)
def _(normalization, data) -> Quantity:
    return data * normalization.max_value


@_apply_normalization.register(NormalizationByValue)
def _(normalization, data) -> Quantity:
    return data * normalization.value


def _get_load_power(
    load: DistributionLoad, ts_data: TimeSeriesData, metadata: TimeSeriesMetadata
) -> Quantity:
    """Internal function to return load power."""
    if metadata.quantity_metadata is None:
        msg = f"The {metadata.type} data is not a GDM quantity: {type(ts_data.data)}"
        raise GDMQuantityError(msg)

    user_attr = UserAttributes.model_validate(metadata.user_attributes)

    # the denormalized data here is the timeseries multiplier of the peak
    # use_actual identifies this as actual time series values rather than multiplier
    denormalized_data = get_timeseries_actual_data(ts_data)
    if user_attr.use_actual:
        return denormalized_data

    if metadata.variable_name in {"active_power", "reactive_power"}:
        return denormalized_data.magnitude.tolist() * sum(
            ph_load.real_power
            if metadata.variable_name == "active_power"
            else ph_load.reactive_power
            for ph_load in load.equipment.phase_loads
        )
    else:
        msg = f"{metadata.variable_name} is not supported for load power calculation."
        raise UnsupportedVariableError(msg)


def _get_solar_power(
    solar: DistributionSolar, ts_data: TimeSeriesData, metadata: TimeSeriesMetadata
) -> Quantity:
    """Internal function to return time series data in kw"""
    if metadata.quantity_metadata is None:
        msg = f"The {metadata.type} data is not a GDM quantity: {type(ts_data.data)}"
        raise GDMQuantityError(msg)

    denormalized_data = get_timeseries_actual_data(ts_data)

    user_attr = UserAttributes.model_validate(metadata.user_attributes)
    if user_attr.use_actual:
        if denormalized_data.units not in {"kilowatt", "watt"}:
            msg = f"Invalid unit for use_actual: {denormalized_data.units}"
            raise GDMQuantityUnitsError(msg)
        return denormalized_data
    dc_power = denormalized_data.to("kilowatt/m^2").magnitude.tolist() * solar.active_power.to(
        "kilowatts"
    )
    return ActivePower(
        np.clip(
            dc_power,
            a_min=ActivePower(0, dc_power.units),
            a_max=solar.equipment.rated_power.to("kilova"),
        ).magnitude,
        dc_power.units,
    )


def _check_for_timeseries_metadata_consistency(ts_metadata: list[TimeSeriesMetadata]):
    # Extract unique properties from ts_data

    user_attrs = [
        UserAttributes.model_validate(metadata.user_attributes) for metadata in ts_metadata
    ]
    unique_props = {
        "profile_type": {user_attr.profile_type for user_attr in user_attrs},
    }
    # Validate uniformity across properties
    if any(len(prop) != 1 for prop in unique_props.values()):
        inconsistent_props = {k: v for k, v in unique_props.items() if len(v) > 1}
        msg = f"Inconsistent timeseries data: {inconsistent_props}"
        raise InconsistentTimeseriesAggregation(msg)


@singledispatch
def _check_for_timeseries_consistency(times_series_sample, ts_list):
    msg = f"Incompatible time series model: {type(times_series_sample)}"
    raise IncompatibleTimeSeries(msg)


@_check_for_timeseries_consistency.register(SingleTimeSeries)
def _(times_series_sample, ts_list) -> None:
    # Extract unique properties from SingleTimeSeries list
    unique_props = {
        "length": {data.length for data in ts_list},
        "resolution": {data.resolution for data in ts_list},
        "start_time": {data.initial_time for data in ts_list},
        "variable": {data.variable_name for data in ts_list},
        "data_type": {type(data.data) for data in ts_list},
    }
    # Validate uniformity across properties
    if any(len(prop) != 1 for prop in unique_props.values()):
        inconsistent_props = {k: v for k, v in unique_props.items() if len(v) > 1}
        msg = f"Inconsistent timeseries data: {inconsistent_props} for {type(times_series_sample)}"
        raise InconsistentTimeseriesAggregation(msg)
    return None


@_check_for_timeseries_consistency.register(NonSequentialTimeSeries)
def _(times_series_sample, ts_list) -> None:
    # Extract unique properties from SingleTimeSeries list
    unique_props = {
        "length": {data.length for data in ts_list},
        "variable": {data.variable_name for data in ts_list},
        "data_type": {type(data.data) for data in ts_list},
        "timestamps_type": {type(data.timestamps) for data in ts_list},
    }

    # Validate uniformity across properties
    if any(len(prop) != 1 for prop in unique_props.values()):
        inconsistent_props = {k: v for k, v in unique_props.items() if len(v) > 1}
        msg = f"Inconsistent timeseries data: {inconsistent_props} for {type(times_series_sample)}"
        raise InconsistentTimeseriesAggregation(msg)
    return None


def get_aggregated_solar_timeseries(
    sys: DistributionSystem,
    solars: list[DistributionSolar],
    var_name: str,
    time_series_type: Type[TimeSeriesData] = SingleTimeSeries,
) -> TimeSeriesData:
    """Method to return aggregated solar time series data.

    Parameters
    ----------
    sys: DistributionSystem
        Instance of the DistributionSystem
    solars: list[DistributionSolar]
        List of solar for aggregating timeseries data.
    var_name: str
        Variable name for which to combine timeseries data.
    time_series_type: Type[TimeSeriesData]
        Type of time series data. Defaults to: SingleTimeSeries

    Returns
    -------
    TimeSeriesData
    """
    if time_series_type.__name__ not in {"SingleTimeSeries", "NonSequentialTimeSeries"}:
        msg = f"Incompatible time series data: {time_series_type.__name__}"
        raise IncompatibleTimeSeries(msg)

    if var_name not in ["irradiance"]:
        msg = f"{var_name=} is not supported for solar timeseries aggregation."
        raise UnsupportedVariableError(msg)

    ts_components: list[TimeSeriesData] = [
        sys.get_time_series(solar, var_name, time_series_type=time_series_type) for solar in solars
    ]
    times_series_sample = ts_components[0]
    _check_for_timeseries_consistency(times_series_sample, ts_components)

    ts_metadata: list[TimeSeriesMetadata] = [
        sys.list_time_series_metadata(solar, var_name, time_series_type=time_series_type)[0]
        for solar in solars
    ]
    _check_for_timeseries_metadata_consistency(ts_metadata)
    ts_solar_data = [
        _get_solar_power(solar, ts_data, metadata)
        for solar, ts_data, metadata in zip(solars, ts_components, ts_metadata)
    ]
    if isinstance(times_series_sample, SingleTimeSeries):
        return SingleTimeSeries(
            data=sum(ts_solar_data),
            variable_name=var_name,
            normalization=None,
            initial_time=times_series_sample.initial_time,
            resolution=times_series_sample.resolution,
        )
    else:
        return NonSequentialTimeSeries(
            data=sum(ts_solar_data),
            timestamps=times_series_sample.timestamps,
            variable_name=var_name,
            normalization=None,
        )


def get_aggregated_battery_timeseries(
    sys: DistributionSystem, batteries: list[DistributionBattery], var_name: str
) -> SingleTimeSeries:
    """Method to return combined battery time series data.

    Parameters
    ----------
    sys: DistributionSystem
        Instance of the DistributionSystem
    batteries: list[DistributionBattery]
        List of battery for aggregating timeseries data.
    var_name: str
        Variable name used for time series aggregation.

    Returns
    -------
    SingleTimeSeries
    """
    ts_components: list[SingleTimeSeries] = [
        sys.get_time_series(battery, var_name) for battery in batteries
    ]
    _check_for_timeseries_consistency(ts_components)
    ts_metadata: list[SingleTimeSeriesMetadata] = [
        sys.list_time_series_metadata(battery, var_name)[0] for battery in batteries
    ]
    _check_for_timeseries_metadata_consistency(ts_metadata)
    ts_battery_data = [
        _get_load_power(battery, ts_data, metadata)
        for battery, ts_data, metadata in zip(batteries, ts_components, ts_metadata)
    ]
    return SingleTimeSeries(
        data=sum(ts_battery_data),
        variable_name=var_name,
        normalization=None,
        initial_time=ts_components[0].initial_time,
        resolution=ts_components[0].resolution,
    )


def get_aggregated_load_timeseries(
    sys: DistributionSystem,
    loads: list[DistributionLoad],
    var_name: str,
    time_series_type: Type[TimeSeriesData] = SingleTimeSeries,
) -> TimeSeriesData:
    """Method to return aggregated load time series data.

    Parameters
    ----------
    sys: DistributionSystem
        Instance of the DistributionSystem
    loads: list[DistributionLoad]
        List of loads for aggregating timeseries data.
    var_name: str
        Variable name used for time series aggregation.
    time_series_type: Type[TimeSeriesData]
        Type of time series data. Defaults to: SingleTimeSeries

    Returns
    -------
    TimeSeriesData
    """
    if time_series_type.__name__ not in {"SingleTimeSeries", "NonSequentialTimeSeries"}:
        msg = f"Incompatible time series data: {time_series_type.__name__}"
        raise IncompatibleTimeSeries(msg)

    ts_components: list[TimeSeriesData] = [
        sys.get_time_series(load, var_name, time_series_type=time_series_type) for load in loads
    ]

    times_series_sample = ts_components[0]

    _check_for_timeseries_consistency(times_series_sample, ts_components)
    ts_metadata: list[TimeSeriesMetadata] = [
        sys.list_time_series_metadata(load, var_name, time_series_type=time_series_type)[0]
        for load in loads
    ]
    _check_for_timeseries_metadata_consistency(ts_metadata)
    ts_load_data = [
        _get_load_power(load, ts_data, metadata)
        for load, ts_data, metadata in zip(loads, ts_components, ts_metadata)
    ]
    if isinstance(times_series_sample, SingleTimeSeries):
        return SingleTimeSeries(
            data=sum(ts_load_data),
            variable_name=var_name,
            normalization=None,
            initial_time=times_series_sample.initial_time,
            resolution=times_series_sample.resolution,
        )
    else:
        return NonSequentialTimeSeries(
            data=sum(ts_load_data),
            timestamps=times_series_sample.timestamps,
            variable_name=var_name,
            normalization=None,
        )


def _get_combined_single_time_series_df(
    sys: DistributionSystem,
    component_type: type,
    var_of_interest: set[str],
    power_function: Callable,
    unit_conversion: dict[str, str],
    time_series_type: Type[TimeSeriesData] = SingleTimeSeries,
) -> pd.DataFrame:
    """
    Generalized function for returning combined single time series dataframe for given component type.

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
    time_series_type: Type[TimeSeriesData]
        Type of time series data. Defaults to: SingleTimeSeries
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
    components: list[Component] = list(sys.get_components(component_type))
    if not components:
        raise NoComponentsFoundError(
            f"No components of type {component_type.__name__} found in {sys.name}"
        )

    for component in components:
        ts_metadata = sys.list_time_series_metadata(component, time_series_type=time_series_type)

        if not ts_metadata:
            msg = f"No timeseries data found for {component=}."
            raise NoTimeSeriesDataFound(msg)

        avail_vars = {md.variable_name for md in ts_metadata}

        if not var_of_interest.issubset(avail_vars):
            msg = f"{avail_vars=}. Only {var_of_interest=} is supported for dataframe computation."
            raise TimeseriesVariableDoesNotExist(msg)

        for var in var_of_interest & avail_vars:
            ts_data: SingleTimeSeries = sys.get_time_series(
                owner=component, variable_name=var, time_series_type=time_series_type
            )
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
                            power_data.to(unit_conversion[var]).magnitude
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


def _get_combined_nonsequential_time_series_df(
    sys: DistributionSystem,
    component_type: type,
    var_of_interest: set[str],
    power_function: Callable,
    unit_conversion: dict[str, str],
    time_series_type: Type[TimeSeriesData] = NonSequentialTimeSeries,
) -> pd.DataFrame:
    """
    Generalized function for returning combined single time series dataframe for given component type.

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
    time_series_type: Type[TimeSeriesData]
        Type of time series data. Defaults to: NonSequentialTimeSeries

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
        If timeseries data is not of type NonSequentialTimeSeries.
    TimeseriesVariableDoesNotExist
        If specified variables do not exist for the given component.
    """
    dfs = []
    components: list[Component] = list(sys.get_components(component_type))
    if not components:
        raise NoComponentsFoundError(
            f"No components of type {component_type.__name__} found in {sys.name}"
        )

    for component in components:
        ts_metadata = sys.list_time_series_metadata(component, time_series_type=time_series_type)

        if not ts_metadata:
            msg = f"No timeseries data found for {component=}."
            raise NoTimeSeriesDataFound(msg)

        avail_vars = {md.variable_name for md in ts_metadata}

        if not var_of_interest.issubset(avail_vars):
            msg = f"{avail_vars=}. Only {var_of_interest=} is supported for dataframe computation."
            raise TimeseriesVariableDoesNotExist(msg)

        for var in var_of_interest & avail_vars:
            ts_data: NonSequentialTimeSeries = sys.get_time_series(
                owner=component, variable_name=var, time_series_type=time_series_type
            )
            metadata = [meta for meta in ts_metadata if meta.variable_name == var][0]
            power_data = power_function(component, ts_data, metadata)
            dfs.append(
                pd.DataFrame(
                    {
                        "timestamp": ts_data.timestamps,
                        "variable_name": [var] * ts_data.length,
                        "component_uuid": [component.uuid] * ts_data.length,
                        "value": (
                            power_data.to(unit_conversion[var]).magnitude
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
    sys: DistributionSystem,
    unit_conversion: dict[str, str],
    var_of_interest: set[str] = {"active_power", "reactive_power"},
    time_series_type: Type[TimeSeriesData] = SingleTimeSeries,
) -> pd.DataFrame:
    """
    Function for returning combined timeseries dataframe for load components.

    Parameters
    ----------
    sys: DistributionSystem
        Instance of DistributionSystem.
    unit_conversion: dict[str, str]
        Optional dictionary to perform unit conversion on data in pint quantities.
    var_of_interest: set[str]
        Set of variable names of interest. Defaults to: {"active_power", "reactive_power"}
    time_series_type: Type[TimeSeriesData]
        Type of time series data. Defaults to: SingleTimeSeries
    Returns
    -------
    pd.DataFrame
    """
    if time_series_type.__name__ == "SingleTimeSeries":
        return _get_combined_single_time_series_df(
            sys=sys,
            component_type=DistributionLoad,
            var_of_interest=var_of_interest,
            power_function=_get_load_power,
            unit_conversion=unit_conversion,
            time_series_type=time_series_type,
        )
    elif time_series_type.__name__ == "NonSequentialTimeSeries":
        return _get_combined_nonsequential_time_series_df(
            sys=sys,
            component_type=DistributionLoad,
            var_of_interest=var_of_interest,
            power_function=_get_load_power,
            unit_conversion=unit_conversion,
            time_series_type=time_series_type,
        )
    else:
        msg = f"get_combined_load_timeseries_df not implemented for {time_series_type.__name__}"
        raise IncompatibleTimeSeries(msg)


def get_combined_solar_timeseries_df(
    sys: DistributionSystem,
    unit_conversion: dict[str, str],
    var_of_interest: set[str] = {"irradiance"},
    time_series_type: Type[TimeSeriesData] = SingleTimeSeries,
) -> pd.DataFrame:
    """
    Function for returning combined timeseries dataframe for solar components.

    Parameters
    ----------
    sys: DistributionSystem
        Instance of DistributionSystem.
    unit_conversion: dict[str, str]
        Optional dictionary to perform unit conversion on data in pint quantities.
    var_of_interest: set[str]
        Set of variable names of interest. Defaults to: {"irradiance"}
    time_series_type: Type[TimeSeriesData]
        Type of time series data. Defaults to: SingleTimeSeries
    Returns
    -------
    pd.DataFrame
    """
    if time_series_type.__name__ == "SingleTimeSeries":
        solar_df = _get_combined_single_time_series_df(
            sys=sys,
            component_type=DistributionSolar,
            var_of_interest=var_of_interest,
            power_function=_get_solar_power,
            unit_conversion=unit_conversion,
            time_series_type=time_series_type,
        )
        return solar_df.replace("irradiance", "active_power")
    elif time_series_type.__name__ == "NonSequentialTimeSeries":
        solar_df = _get_combined_nonsequential_time_series_df(
            sys=sys,
            component_type=DistributionSolar,
            var_of_interest=var_of_interest,
            power_function=_get_solar_power,
            unit_conversion=unit_conversion,
            time_series_type=time_series_type,
        )
        return solar_df.replace("irradiance", "active_power")
    else:
        msg = f"get_combined_load_timeseries_df not implemented for {time_series_type.__name__}"
        raise IncompatibleTimeSeries(msg)
