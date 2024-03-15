"""This module contains basic model for distribution substation."""

from typing import Annotated

from infrasys.component_models import ComponentWithQuantities
from pydantic import Field

from gdm.distribution.components.distribution_feeder import DistributionFeeder


class DistributionSubstation(ComponentWithQuantities):
    """Class interface for distribution feeder."""

    feeders: Annotated[
        list[DistributionFeeder], Field(..., description="List of feeders for this substation.")
    ]

    @classmethod
    def example(cls) -> "DistributionSubstation":
        return DistributionSubstation(
            name="Test Substation",
            feeders=[DistributionFeeder.example()],
        )
