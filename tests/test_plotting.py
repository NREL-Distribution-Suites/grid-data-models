import random

from gdm.distribution.enums import ColorNodeBy, ColorLineBy
from gdm.distribution.components import DistributionBus
from gdm.distribution import DistributionSystem
import pytest

SHOW = False


def random_lat_lon():
    lat = random.uniform(-90, 90)  # Latitude range from -90 to 90
    lon = random.uniform(-180, 180)  # Longitude range from -180 to 180
    return lat, lon


def test_gdf_conversion(distribution_system_with_single_timeseries, tmp_path):
    model: DistributionSystem = distribution_system_with_single_timeseries
    buses = model.get_components(DistributionBus)
    model.name = "test_model"
    for bus in buses:
        bus.coordinate.x, bus.coordinate.y = random_lat_lon()
        bus.coordinate.crs = "epsg:4326"

    exported_file = tmp_path / f"{model.name}_gdf.csv"
    system_gdf = model.to_gdf()

    assert not exported_file.exists()

    assert not system_gdf.empty
    assert system_gdf.shape == (41, 8), "Expected 41 rows and 8 columns. Got {}".format(
        system_gdf.shape
    )

    model.to_gdf(tmp_path / f"{model.name}_gdf.csv")
    assert (tmp_path / f"{model.name}_gdf.csv").exists()
    model.to_geojson(tmp_path / f"{model.name}_gdf.geojson")
    assert (tmp_path / f"{model.name}_gdf.geojson").exists()


def test_system_gdf_failure(distribution_system_with_single_timeseries, tmp_path):
    model: DistributionSystem = distribution_system_with_single_timeseries
    buses = model.get_components(DistributionBus)
    model.name = "test_model"
    for bus in buses:
        bus.coordinate.x, bus.coordinate.y = random_lat_lon()
        bus.coordinate.crs = "epsg:4326"

    with pytest.raises(FileNotFoundError):
        model.plot(tmp_path / "test_model_plot.html", zoom_level=1, show=SHOW)


def test_system_plotting(distribution_system_with_single_timeseries, tmp_path):
    model: DistributionSystem = distribution_system_with_single_timeseries
    buses = model.get_components(DistributionBus)
    model.name = "test_model"
    for bus in buses:
        bus.coordinate.x, bus.coordinate.y = random_lat_lon()
        bus.coordinate.crs = "epsg:4326"
    model.plot(tmp_path, zoom_level=1, show=SHOW, color_node_by=ColorNodeBy.PHASE)
    export_path = tmp_path / "test_model_plot.html"
    assert export_path.exists()

    model.name = "test_model_1"
    model.plot(tmp_path, zoom_level=1, show=SHOW, color_node_by=ColorNodeBy.EQUIPMENT_TYPE)
    export_path = tmp_path / "test_model_1_plot.html"
    assert export_path.exists()

    model.name = "test_model_2"
    model.plot(tmp_path, zoom_level=1, show=SHOW, color_node_by=ColorNodeBy.VOLTAGE_LEVEL)
    export_path = tmp_path / "test_model_2_plot.html"
    assert export_path.exists()

    model.name = "test_model_3"
    model.plot(tmp_path, zoom_level=1, show=SHOW, color_line_by=ColorLineBy.EQUIPMENT_TYPE)
    export_path = tmp_path / "test_model_3_plot.html"
    assert export_path.exists()

    model.name = "test_model_4"
    model.plot(tmp_path, zoom_level=1, show=SHOW, color_line_by=ColorLineBy.PHASE)
    export_path = tmp_path / "test_model_4_plot.html"
    assert export_path.exists()

    model.name = "test_model_5"
    model.plot(
        tmp_path,
        zoom_level=1,
        show=SHOW,
        color_line_by=ColorLineBy.DEFAULT,
        color_node_by=ColorNodeBy.DEFAULT,
    )
    export_path = tmp_path / "test_model_5_plot.html"
    assert export_path.exists()

    model.name = "test_model_6"
    model.plot(tmp_path, show=SHOW, flip_coordinates=True)
    export_path = tmp_path / "test_model_6_plot.html"
    assert export_path.exists()

    model.name = "test_model_7"
    model.plot(tmp_path, show=SHOW, flip_coordinates=False)
    export_path = tmp_path / "test_model_7_plot.html"
    assert export_path.exists()

    with pytest.raises(NotADirectoryError):
        model.plot(tmp_path / "test_model_plot.html", zoom_level=1, show=SHOW)


def test_system_plotting_failure(distribution_system_with_single_timeseries, tmp_path):
    model: DistributionSystem = distribution_system_with_single_timeseries
    buses = model.get_components(DistributionBus)
    model.name = "test_model"
    for bus in buses:
        bus.coordinate.x, bus.coordinate.y = random_lat_lon()
        bus.coordinate.crs = "epsg:4326"

    with pytest.raises(FileNotFoundError):
        model.plot(tmp_path / "test_model_plot.html", zoom_level=1, show=SHOW)
