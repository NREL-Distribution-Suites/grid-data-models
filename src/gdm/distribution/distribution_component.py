""" This module contains class for managing basic fields for distribution assets."""

from typing_extensions import Annotated

from pydantic import Field
from infrasys.component_models import Component


class DistributionComponent(Component):
    """Interface for simple distribution component."""

    substation: Annotated[str, Field(..., description="Name of the substation.")]
    feeder: Annotated[str, Field(..., description="Name of the feeder.")]

    @classmethod
    def example(cls) -> "DistributionComponent":
        return DistributionComponent(substation="Dodo Substation", feeder="Duck feeder")
