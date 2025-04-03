from infrasys.time_series_models import SingleTimeSeries, NonSequentialTimeSeries

from gdm.distribution.components import DistributionLoad, DistributionSolar
from gdm.distribution.model_reduction import reduce_to_three_phase_system
from gdm.distribution import DistributionSystem

def test_serialization_deserialization_single_time_series(
    tmp_path, distribution_system_with_single_timeseries
):
    system = distribution_system_with_single_timeseries
    components = list(system.iter_all_components())
    num_components = len(components)

    filename = tmp_path / "system.json"
    system.to_json(filename, overwrite=True)
    system2 = DistributionSystem.from_json(filename)
    components2 = list(system2.iter_all_components())
    assert len(components2) == num_components
    # NOTE: AP: __eq__ is not implemented for "equipment" models in gdm
    # so it is tough to check if two equipment are equal
    for component in components:
        if isinstance(component, (DistributionLoad)):
            component2 = system2.get_component_by_uuid(component.uuid)
            ts1_active = system.get_time_series(
                component, variable_name="active_power", time_series_type=SingleTimeSeries
            )
            ts2_active = system2.get_time_series(
                component2, variable_name="active_power", time_series_type=SingleTimeSeries
            )
            ts1_reactive = system.get_time_series(
                component, variable_name="reactive_power", time_series_type=SingleTimeSeries
            )
            ts2_reactive = system2.get_time_series(
                component2, variable_name="reactive_power", time_series_type=SingleTimeSeries
            )
            assert ts1_active == ts2_active
            assert ts1_reactive == ts2_reactive

        if isinstance(component, (DistributionSolar)):
            component2 = system2.get_component_by_uuid(component.uuid)
            ts1 = system.get_time_series(
                component, variable_name="irradiance", time_series_type=SingleTimeSeries
            )
            ts2 = system2.get_time_series(
                component2, variable_name="irradiance", time_series_type=SingleTimeSeries
            )
            assert ts1 == ts2


def test_serialization_deserialization_non_sequential_time_series(
    tmp_path, distribution_system_with_nonsequential_timeseries
):
    system = distribution_system_with_nonsequential_timeseries
    components = list(system.iter_all_components())
    num_components = len(components)

    filename = tmp_path / "system.json"
    system.to_json(filename, overwrite=True)
    system2 = DistributionSystem.from_json(filename)
    components2 = list(system2.iter_all_components())
    assert len(components2) == num_components
    for component in components:
        if isinstance(component, (DistributionLoad)):
            component2 = system2.get_component_by_uuid(component.uuid)
            ts1_active = system.get_time_series(
                component, variable_name="active_power", time_series_type=NonSequentialTimeSeries
            )
            ts2_active = system2.get_time_series(
                component2, variable_name="active_power", time_series_type=NonSequentialTimeSeries
            )
            ts1_reactive = system.get_time_series(
                component, variable_name="reactive_power", time_series_type=NonSequentialTimeSeries
            )
            ts2_reactive = system2.get_time_series(
                component2,
                variable_name="reactive_power",
                time_series_type=NonSequentialTimeSeries,
            )
            assert ts1_active == ts2_active
            assert ts1_reactive == ts2_reactive

        if isinstance(component, (DistributionSolar)):
            component2 = system2.get_component_by_uuid(component.uuid)
            ts1 = system.get_time_series(
                component, variable_name="irradiance", time_series_type=NonSequentialTimeSeries
            )
            ts2 = system2.get_time_series(
                component2, variable_name="irradiance", time_series_type=NonSequentialTimeSeries
            )
            assert ts1 == ts2


def test_serialization_deserialization_single_time_series_with_reduction(
    tmp_path, distribution_system_with_single_timeseries
):
    gdm_system: DistributionSystem = distribution_system_with_single_timeseries
    system = reduce_to_three_phase_system(
        gdm_system,
        name="reduced_system_single_ts",
        agg_timeseries=True,
        time_series_type=SingleTimeSeries,
    )
    components = list(system.iter_all_components())
    num_components = len(components)

    filename = tmp_path / "system.json"
    system.to_json(filename, overwrite=True)
    system2 = DistributionSystem.from_json(filename)
    components2 = list(system2.iter_all_components())
    assert len(components2) == num_components
    for _, component in enumerate(components):
        if isinstance(component, (DistributionLoad)):
            component2 = system2.get_component_by_uuid(component.uuid)
            ts1_active = system.get_time_series(
                component, variable_name="active_power", time_series_type=SingleTimeSeries
            )
            ts2_active = system2.get_time_series(
                component2, variable_name="active_power", time_series_type=SingleTimeSeries
            )
            ts1_reactive = system.get_time_series(
                component, variable_name="reactive_power", time_series_type=SingleTimeSeries
            )

            ts2_reactive = system2.get_time_series(
                component2, variable_name="reactive_power", time_series_type=SingleTimeSeries
            )
            assert ts1_active == ts2_active
            assert ts1_reactive == ts2_reactive

        if isinstance(component, (DistributionSolar)):
            component2 = system2.get_component_by_uuid(component.uuid)
            ts1 = system.get_time_series(
                component, variable_name="irradiance", time_series_type=SingleTimeSeries
            )
            ts2 = system2.get_time_series(
                component2, variable_name="irradiance", time_series_type=SingleTimeSeries
            )
            assert ts1 == ts2


def test_serialization_deserialization_non_sequential_time_series_with_reduction(
    tmp_path, distribution_system_with_nonsequential_timeseries
):
    gdm_system: DistributionSystem = distribution_system_with_nonsequential_timeseries
    system = reduce_to_three_phase_system(
        gdm_system,
        name="reduced_system_nonsequential_ts",
        agg_timeseries=True,
        time_series_type=NonSequentialTimeSeries,
    )
    components = list(system.iter_all_components())
    num_components = len(components)

    filename = tmp_path / "system.json"
    system.to_json(filename, overwrite=True)
    system2 = DistributionSystem.from_json(filename)
    components2 = list(system2.iter_all_components())
    assert len(components2) == num_components
    for component in components:
        if isinstance(component, (DistributionLoad)):
            component2 = system2.get_component_by_uuid(component.uuid)
            ts1_active = system.get_time_series(
                component, variable_name="active_power", time_series_type=NonSequentialTimeSeries
            )
            ts2_active = system2.get_time_series(
                component2, variable_name="active_power", time_series_type=NonSequentialTimeSeries
            )
            ts1_reactive = system.get_time_series(
                component, variable_name="reactive_power", time_series_type=NonSequentialTimeSeries
            )
            ts2_reactive = system2.get_time_series(
                component2,
                variable_name="reactive_power",
                time_series_type=NonSequentialTimeSeries,
            )
            assert ts1_active == ts2_active
            assert ts1_reactive == ts2_reactive

        if isinstance(component, (DistributionSolar)):
            component2 = system2.get_component_by_uuid(component.uuid)
            ts1 = system.get_time_series(
                component, variable_name="irradiance", time_series_type=NonSequentialTimeSeries
            )
            ts2 = system2.get_time_series(
                component2, variable_name="irradiance", time_series_type=NonSequentialTimeSeries
            )
            assert ts1 == ts2
