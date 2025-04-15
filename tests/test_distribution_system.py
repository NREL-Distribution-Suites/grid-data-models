from gdm.distribution import DistributionSystem


def test_distribution_system_with_timeseries(distribution_system_with_single_timeseries):
    """Tests creation of sample distribution system with timeseries."""
    assert isinstance(distribution_system_with_single_timeseries, DistributionSystem)
