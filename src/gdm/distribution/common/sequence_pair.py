from typing import NamedTuple

from pydantic import NonNegativeInt


class SequencePair(NamedTuple):
    """Interface for defining named tuple for sequence pair."""

    from_index: NonNegativeInt
    to_index: NonNegativeInt
