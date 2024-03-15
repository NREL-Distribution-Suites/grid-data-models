"""This module has contains all common models used in
distribution subpackage."""

from typing import Annotated, Optional

from pydantic import Field

from gdm.distribution.components.distribution_component import DistributionComponent


BELONG_TO_TYPE = Annotated[
    Optional[DistributionComponent],
    Field(
        None,
        description="Provides info about substation and feeder. ",
    ),
]
