""" This module contains class for managing basic fields for distribution assets."""

from typing_extensions import Annotated
from typing import Optional
from abc import ABC

from pydantic import Field
from infrasys import Component

from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation


class DistributionComponentBase(Component, ABC):
    """Interface for simple distribution component."""

    substation: Annotated[
        Optional[DistributionSubstation], Field(None, description="Name of the substation.")
    ]
    feeder: Annotated[Optional[DistributionFeeder], Field(None, description="Name of the feeder.")]
