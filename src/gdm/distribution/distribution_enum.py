""" This module contains phase enums. """

from enum import Enum


class Phase(str, Enum):
    """This class is used to represent a single phase from a set of possible values."""

    A = "A"
    B = "B"
    C = "C"
    N = "N"
    S1 = "S1"
    S2 = "S2"


class ConnectionType(str, Enum):
    """Interface for connection type."""

    STAR = "STAR"
    DELTA = "DELTA"
    OPEN_DELTA = "OPEN_DELTA"
    OPEN_STAR = "OPEN_STAR"
    ZIG_ZAG = "ZIG_ZAG"


class VoltageTypes(str, Enum):
    """Interface for voltage types."""

    LINE_TO_LINE = "line-to-line"
    LINE_TO_GROUND = "line-to-ground"


class LimitType(str, Enum):
    """Interface for operational limit types."""

    MIN = "min"
    MAX = "max"
