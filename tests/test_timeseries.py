from datetime import datetime, timedelta

from infrasys.time_series_models import SingleTimeSeries
from infrasys.quantities import ActivePower
import pandas as pd

from gdm.distribution.distribution_system import DistributionSystem
from .models.simple_system import SimpleBus, SimpleGenerator


def test_combined_dataframe():
    sys = DistributionSystem(auto_add_composed_components=True)
    bus1 = SimpleBus(name="bus1", voltage=12.47)
    bus2 = SimpleBus(name="bus2", voltage=12.47)
    gen1 = SimpleGenerator(name="gen1", available=True, bus=bus1, active_power=1.0, rating=1.0)
    gen2 = SimpleGenerator(name="gen2", available=True, bus=bus2, active_power=1.0, rating=1.0)
    sys.add_components(gen1, gen2)
    data = ActivePower([1.0, 2.0, 3.0, 4.0, 5.0], "watts")
    resolution = timedelta(hours=1)
    start_time = datetime(2024, 1, 1, 0, 0, 0)
    for var_name in ["active_power", "active_power_2"]:
        ts = SingleTimeSeries(
            variable_name=var_name,
            data=data,
            resolution=resolution,
            initial_time=start_time,
        )
        sys.add_time_series(ts, gen1, gen2)

    gen_df = sys.get_combined_timeseries_df(
        SimpleGenerator,
        unit_conversion={
            "active_power": "kilowatts",
            "active_power_2": "kilowatts",
        },
    )
    assert isinstance(gen_df, pd.DataFrame)
    assert set(gen_df.columns) == {
        "timestamp",
        "component_uuid",
        "variable_name",
        "value",
        "units",
    }
    assert len(gen_df) == 20
