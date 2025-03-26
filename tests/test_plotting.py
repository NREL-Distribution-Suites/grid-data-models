import random

from gdm import DistributionSystem, DistributionBus
from gdm.distribution.distribution_enum import ColorNodeBy, ColorLineBy
import pytest


def random_lat_lon():
    lat = random.uniform(-90, 90)  # Latitude range from -90 to 90
    lon = random.uniform(-180, 180)  # Longitude range from -180 to 180
    return lat, lon


def test_gdf_conversion(sample_distribution_system_with_timeseries, tmp_path):
    model: DistributionSystem = sample_distribution_system_with_timeseries
    buses = model.get_components(DistributionBus)
    model.name = "test_model"
    for bus in buses:
        bus.coordinate.x, bus.coordinate.y = random_lat_lon()
        bus.coordinate.crs = "epsg:4326"

    nodes_gdf, edges_gdf = model.to_gdf(tmp_path)
    assert not nodes_gdf.empty
    assert not edges_gdf.empty
    assert edges_gdf.shape == (20, 7), "Expected 20 rows and 7 columns. Got {}".format(
        edges_gdf.shape
    )
    assert nodes_gdf.shape == (21, 7), "Expected 21 rows and 7 columns. Got {}".format(
        nodes_gdf.shape
    )

    with pytest.raises(NotADirectoryError):
        model.to_gdf(tmp_path / "test_model_edges_gdf.csv")


def test_system_gdf_failure(sample_distribution_system_with_timeseries, tmp_path):
    model: DistributionSystem = sample_distribution_system_with_timeseries
    buses = model.get_components(DistributionBus)
    model.name = "test_model"
    for bus in buses:
        bus.coordinate.x, bus.coordinate.y = random_lat_lon()
        bus.coordinate.crs = "epsg:4326"

    with pytest.raises(FileNotFoundError):
        model.plot(tmp_path / "test_model_plot.html", zoom_level=1, show=False)


def test_system_plotting(sample_distribution_system_with_timeseries, tmp_path):
    model: DistributionSystem = sample_distribution_system_with_timeseries
    buses = model.get_components(DistributionBus)
    model.name = "test_model"
    for bus in buses:
        bus.coordinate.x, bus.coordinate.y = random_lat_lon()
        bus.coordinate.crs = "epsg:4326"

    model.plot(tmp_path, zoom_level=1, show=False, color_node_by=ColorNodeBy.PHASE)
    export_path = tmp_path / "test_model_plot.html"
    assert export_path.exists()

    model.name = "test_model_1"
    model.plot(tmp_path, zoom_level=1, show=False, color_node_by=ColorNodeBy.TYPE)
    export_path = tmp_path / "test_model_1_plot.html"
    assert export_path.exists()

    model.name = "test_model_2"
    model.plot(tmp_path, zoom_level=1, show=False, color_node_by=ColorNodeBy.VOLTAGE_LEVEL)
    export_path = tmp_path / "test_model_2_plot.html"
    assert export_path.exists()

    model.name = "test_model_3"
    model.plot(tmp_path, zoom_level=1, show=False, color_line_by=ColorLineBy.TYPE)
    export_path = tmp_path / "test_model_3_plot.html"
    assert export_path.exists()

    model.name = "test_model_4"
    model.plot(tmp_path, zoom_level=1, show=False, color_line_by=ColorLineBy.PHASE)
    export_path = tmp_path / "test_model_4_plot.html"
    assert export_path.exists()

    with pytest.raises(NotADirectoryError):
        model.plot(tmp_path / "test_model_plot.html", zoom_level=1, show=False)


def test_system_plotting_failure(sample_distribution_system_with_timeseries, tmp_path):
    model: DistributionSystem = sample_distribution_system_with_timeseries
    buses = model.get_components(DistributionBus)
    model.name = "test_model"
    for bus in buses:
        bus.coordinate.x, bus.coordinate.y = random_lat_lon()
        bus.coordinate.crs = "epsg:4326"

    with pytest.raises(FileNotFoundError):
        model.plot(tmp_path / "test_model_plot.html", zoom_level=1, show=False)
