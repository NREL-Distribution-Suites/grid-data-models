from gdm.distribution import DistributionSystem
from gdm.distribution.components import GeometryBranch, MatrixImpedanceBranch


def test_distribution_system_with_time_series(distribution_system_with_single_time_series):
    """Tests creation of sample distribution system with time series."""

    assert isinstance(distribution_system_with_single_time_series, DistributionSystem)


def test_geometry_conversion(distribution_system_with_single_time_series):
    """Tests creation of sample distribution system with time series."""

    sys = distribution_system_with_single_time_series
    assert len(list(sys.get_components(MatrixImpedanceBranch))) == 18
    assert len(list(sys.get_components(GeometryBranch))) == 0
    branch = sys.get_component(MatrixImpedanceBranch, "line_bus_8_bus_9")
    new_branch = GeometryBranch.example()
    new_branch.buses = branch.buses
    sys.remove_component(branch)
    sys.add_component(new_branch)
    assert len(list(sys.get_components(MatrixImpedanceBranch))) == 17
    assert len(list(sys.get_components(GeometryBranch))) == 1
    sys.convert_geometry_to_matrix_representation()
    assert len(list(sys.get_components(MatrixImpedanceBranch))) == 18
    assert len(list(sys.get_components(GeometryBranch))) == 0
