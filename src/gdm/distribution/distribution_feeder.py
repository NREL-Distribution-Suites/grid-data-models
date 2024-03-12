""" This module contains pydantic model for distribution feeder. """

from infrasys.component_models import ComponentWithQuantities


class DistributionFeeder(ComponentWithQuantities):
    """Class interface for distribution feeder."""

    @classmethod
    def example(cls) -> "DistributionFeeder":
        return DistributionFeeder(name="Test Feeder")
