""" Module for storing enums. """

# standard imports
from enum import Enum

class Phase(str, Enum):
    """This class is used to represent a single phase from a set of possible values."""

    A = "A"
    B = "B"
    C = "C"
    N = "N"
    s1 = "s1"
    s2 = "s2"