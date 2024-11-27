from gdm import DistributionSystem


def test_distribution_system_with_timeseries(sample_distribution_system_with_timeseries):
    """Tests creation of sample distribution system with timeseries."""
    assert isinstance(sample_distribution_system_with_timeseries, DistributionSystem)
