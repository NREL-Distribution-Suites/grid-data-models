"""This module contains phase enums."""

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
    """Winding connection types."""

    STAR = "STAR"
    DELTA = "DELTA"
    OPEN_DELTA = "OPEN_DELTA"
    OPEN_STAR = "OPEN_STAR"
    ZIG_ZAG = "ZIG_ZAG"


class VoltageTypes(str, Enum):
    """Identifier of voltage types referenced in distribution models."""

    LINE_TO_LINE = "line-to-line"
    LINE_TO_GROUND = "line-to-ground"


class LimitType(str, Enum):
    """Operational limit types."""

    MIN = "min"
    MAX = "max"


class BatteryState(str, Enum):
    """Repersents possible battery operation states."""

    CHARGING = "charging"
    DISCHARGING = "discharging"
    IDLING = "idling"


class ControllerSupport(str, Enum):
    """Identifier for distribution components supported by the control algorithm"""

    BATTERY_ONLY = "battery-only"
    SOLAR_ONLY = "solar-only"
    BATTERY_AND_SOLAR = "battery-and-solar"


class ColorNodeBy(str, Enum):
    """Node color choices for the distribution system plot"""

    PHASE = "Phases"
    DEFAULT = "Default"
    EQUIPMENT_TYPE = "Type"
    VOLTAGE_LEVEL = "kV"


class ColorLineBy(str, Enum):
    """Line color choices for the distribution system plot"""

    PHASE = "Phases"
    DEFAULT = "Default"
    EQUIPMENT_TYPE = "Type"
