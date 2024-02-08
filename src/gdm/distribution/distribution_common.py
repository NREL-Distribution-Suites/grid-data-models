"""This module has contains all common models used in
distribution subpackage."""

from typing import Annotated, NamedTuple, Optional

from pydantic import Field, NonNegativeInt

from gdm.distribution.distribution_component import DistributionComponent


class SequencePair(NamedTuple):
    """Interface for defining named tuple for sequence pair."""

    from_index: NonNegativeInt
    to_index: NonNegativeInt


BELONG_TO_TYPE = Annotated[
    Optional[DistributionComponent],
    Field(
        None,
        description="Provides info about substation and feeder. ",
    ),
]
