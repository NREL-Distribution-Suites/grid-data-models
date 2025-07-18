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


class TransformerMounting(str, Enum):
    """Transformer mounting type."""

    POLE_MOUNT = "POLE_MOUNT"
    PAD_MOUNT = "PAD_MOUNT"
    UNDERGROUND_VAULT = "UNDERGROUND_VAULT"


class LineType(str, Enum):
    """Line type."""

    OVERHEAD = "OVERHEAD"
    UNDERGROUND = "UNDERGROUND"


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


class MapType(str, Enum):
    """Map type choices for the distribution system plot"""

    SCATTER_MAP = "Scattermap"
    SCATTER_GEO = "Scattergeo"


class PlotingStyle(str, Enum):
    CARTO_DARKMATTER = "carto-darkmatter"
    OPEN_STREET_MAP = "open-street-map"
    CARTO_POSITRON = "carto-positron"
    WHITE_BG = "white-bg"


class WireInsulationType(Enum):
    AIR = 1.0  # Air insulation
    PVC = 3.18  # Polyvinyl Chloride
    XLPE = 2.3  # Cross-Linked Polyethylene
    EPR = 2.5  # Ethylene Propylene Rubber
    PE = 2.25  # Polyethylene
    TEFLON = 2.1  # PTFE (Polytetrafluoroethylene)
    SILICONE_RUBBER = 3.5  # Silicone Rubber
    PAPER = 3.7  # Oil-impregnated paper
    MICA = 6.0  # Mica-based insulation


class TOUPeriodType(str, Enum):
    PEAK = "peak"
    OFF_PEAK = "off_peak"
    MID_PEAK = "mid_peak"


class Season(str, Enum):
    SUMMER = "summer"
    WINTER = "winter"
    SHOULDER = "shoulder"


class CustomerClass(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"


class BillingDemandBasis(str, Enum):
    PEAK_15MIN = "peak_15min"
    PEAK_HOUR = "peak_hour"
    CONTRACT_DEMAND = "contract_demand"
