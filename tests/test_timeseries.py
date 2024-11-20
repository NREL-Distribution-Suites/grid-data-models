from pathlib import Path

import pandas as pd

from gdm.distribution.components.distribution_load import DistributionLoad
from gdm.distribution.components.distribution_solar import DistributionSolar
from gdm.distribution.distribution_system import DistributionSystem


def test_combined_timeseries_on_smartds():
    data_path = Path(__file__).parent / "data/p5r_pv.json"
    gdm_sys: DistributionSystem = DistributionSystem.from_json(data_path)
    load_df = gdm_sys.get_combined_timeseries_df(DistributionLoad)
    solar_df = gdm_sys.get_combined_timeseries_df(DistributionSolar)
    assert isinstance(load_df, pd.DataFrame)
    assert isinstance(solar_df, pd.DataFrame)
