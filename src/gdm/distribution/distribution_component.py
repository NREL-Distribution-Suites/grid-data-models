""" This module contains class for managing basic fields for distribution assets."""

from abc import ABC

from infrasys.component_models import Component


class DistributionComponent(Component, ABC):
    """Interface for simple distribution component."""

    substation: str
    feeder: str

    @classmethod
    def example(cls) -> "DistributionComponent":
        return DistributionComponent(substation="Dodo Substation", feeder="Duck feeder")
