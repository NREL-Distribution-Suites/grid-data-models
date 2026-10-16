from gdm.distribution import DistributionSystem
import gdm

import gdm.version


def test_version_control(tmp_path, distribution_system_with_single_time_series):
    system: DistributionSystem = distribution_system_with_single_time_series
    filename = tmp_path / "model.json"
    system.to_json(filename)

    new_system = DistributionSystem.from_json(filename)

    assert new_system.data_format_version == gdm.version.VERSION
