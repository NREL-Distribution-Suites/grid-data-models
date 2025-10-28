from gdm.distribution import DistributionSystem
import gdm
import json

import gdm.version


def test_version_control(tmp_path, distribution_system_with_single_timeseries):
    system: DistributionSystem = distribution_system_with_single_timeseries
    assert system.data_format_version == gdm.version.VERSION.split("+")[0].split("-")[0]
    system.to_json(tmp_path / "model.json")
    with open(tmp_path / "model.json", "r") as f:
        data = json.load(f)
        data["data_format_version"] = "1.0.0"

    with open(tmp_path / "model.json", "w") as file:
        json.dump(data, file, indent=4)

    new_system = DistributionSystem.from_json(tmp_path / "model.json")
    assert new_system.data_format_version == gdm.version.VERSION.split("+")[0].split("-")[0]
