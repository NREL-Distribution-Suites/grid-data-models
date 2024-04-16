""" This module contains class for managing basic fields for distribution assets."""

from typing_extensions import Annotated
from typing import Optional

from pydantic import Field
from infrasys import Component

from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation


class DistributionComponent(Component):
    """Interface for simple distribution component."""

    name: Annotated[str, Field("", description="Name of the component.")]
    substation: Annotated[
        Optional[DistributionSubstation], Field(None, description="Name of the substation.")
    ]
    feeder: Annotated[Optional[DistributionFeeder], Field(None, description="Name of the feeder.")]

    @classmethod
    def example(cls) -> "DistributionComponent":
        return DistributionComponent(
            substation=DistributionSubstation.example(), feeder=DistributionFeeder.example()
        )
