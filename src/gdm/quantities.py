""" This module contains all custom quantities for this package."""

# pylint:disable=unused-argument
# pylint:disable=super-init-not-called

import numpy as np

from infrasys.base_quantity import BaseQuantity, ureg
from infrasys.quantities import Current, Distance, Resistance, Voltage, ActivePower


ureg.define("var = ampere * volt")
ureg.define("va = ampere * volt")


class PositiveResistance(Resistance):
    """Quantity representing power system resistance."""

    def __init__(self, value, units, **kwargs):
        assert value >= 0, f"Resistance ({value}, {units}) must be positive."


class ResistancePULength(BaseQuantity):
    """Quantity representing per unit length power system resistance."""

    __compatible_unit__ = "ohm/m"


class PositiveResistancePULength(ResistancePULength):
    """Quantity representing per unit length positive resistance."""

    def __init__(self, value, units, **kwargs):
        assert all(
            np.array(value).flatten() >= 0
        ), f"Resistance per unit length ({value}, {units}) must be positive."


class Reactance(Resistance):
    """Quantity representing power system reactance."""


class ReactancePULength(BaseQuantity):
    """Quantity representing per unit length power system reactance."""

    __compatible_unit__ = "ohm/m"


class PositiveReactancePULength(ReactancePULength):
    """Quantity representing per unit length positive power system reactance."""

    def __init__(self, value, units, **kwargs):
        assert all(
            np.array(value).flatten() >= 0
        ), f"Reactance per unit length ({value}, {units}) must be positive."


class PositiveReactance(PositiveResistance):
    """Quantity representing positive power system reactance."""

    def __init__(self, value, units, **kwargs):
        assert all(
            np.array(value).flatten() >= 0
        ), f"Reactance ({value}, {units}) must be positive."


class Capacitance(BaseQuantity):
    """Quantity representing power system capacitance."""

    __compatible_unit__ = "farad"


class CapacitancePULength(BaseQuantity):
    """Quantity representing per unit length power system capacitance."""

    __compatible_unit__ = "farad/m"


class PositiveCapacitancePULength(CapacitancePULength):
    """Quantity representing per unit length positive capacitance."""

    def __init__(self, value, units, **kwargs):
        assert all(
            np.array(value).flatten() >= 0
        ), f"Per unit capacitance ({value}, {units}) must be positive."


class PositiveCapacitance(Capacitance):
    """Quantity represening positive capacitance."""

    def __init__(self, value, units, **kwargs):
        assert all(
            np.array(value).flatten() >= 0
        ), f"Capacitance ({value}, {units}) must be positive."


class ReactivePower(BaseQuantity):
    """Quantity representing reactive power."""

    __compatible_unit__ = "var"


class PositiveReactivePower(ReactivePower):
    """Quantity representing positive reactive power."""

    def __init__(self, value, units, **kwargs):
        assert all(
            np.array(value).flatten() >= 0
        ), f"Reactive power ({value}, {units}) must be positive."


class ApparentPower(BaseQuantity):
    """Quantity representing apparent power."""

    __compatible_unit__ = "va"


class PositiveApparentPower(ApparentPower):
    """Quantity representing positive apparent power."""

    def __init__(self, value, units, **kwargs):
        assert all(
            np.array(value).flatten() >= 0
        ), f"Apparent power ({value}, {units}) must be positive."


# TODO: Should these get added to infrasys rather than here?


class PositiveActivePower(ActivePower):
    def __init__(self, value, units, **kwargs):
        assert all(
            np.array(value).flatten() >= 0
        ), f"Active power ({value}, {units}) must be positive."


class PositiveCurrent(Current):
    """Qauntity representing positive current."""

    def __init__(self, value, units, **kwargs):
        assert all(np.array(value).flatten() >= 0), f"Current ({value}, {units}) must be positive."


class PositiveVoltage(Voltage):
    """Quantity representing positive voltage."""

    def __init__(self, value, units, **kwargs):
        assert all(np.array(value).flatten() >= 0), f"Voltage ({value}, {units}) must be positive."


class PositiveDistance(Distance):
    """Quantity representing positive distance."""

    def __init__(self, value, units, **kwargs):
        assert all(
            np.array(value).flatten() >= 0
        ), f"Distance ({value}, {units}) must be positive."


class ActivePowerPUTime(BaseQuantity):
    """Quantity representing active power per unit of time"""

    __compatible_unit__ = "watt/minute"


class Irradiance(BaseQuantity):
    """Quantity representing irradiance in kilowatt per meter**2"""

    __compatible_unit__ = "kilowatt/meter**2"
