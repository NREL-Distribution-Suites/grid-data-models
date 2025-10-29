from gdm.distribution import DistributionSystem
import gdm
import json

import gdm.version

def fix_version(version):
    if version.count('.') >= 3:
        return version.rsplit('.', 1)[0]
    return version



def test_version_control(tmp_path, distribution_system_with_single_timeseries):
    system: DistributionSystem = distribution_system_with_single_timeseries
    assert fix_version(system.data_format_version) == fix_version(gdm.version.VERSION)
    system.to_json(tmp_path / "model.json")
    with open(tmp_path / "model.json", "r") as f:
        data = json.load(f)
        data["data_format_version"] = "1.0.0"

    with open(tmp_path / "model.json", "w") as file:
        json.dump(data, file, indent=4)

    new_system = DistributionSystem.from_json(tmp_path / "model.json")
    assert fix_version(new_system.data_format_version) == fix_version(gdm.version.VERSION)
