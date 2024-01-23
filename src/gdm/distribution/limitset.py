""" This module contains interface for operation limit sets. """
from typing import Literal

from infrasys.component_models import Component

from gdm.quantities import PositiveCurrent, PositiveVoltage


class VoltageLimitSet(Component):
    """Interface for voltage limit set."""

    limit_type: Literal["min", "max"]
    value: PositiveVoltage

    @classmethod
    def example(cls) -> "VoltageLimitSet":
        return VoltageLimitSet(limit_type="min", value=PositiveVoltage(400 * 0.9, "volt"))


class ThermalLimitSet(Component):
    """Interface for voltage limit set."""

    limit_type: Literal["max"]
    value: PositiveCurrent

    @classmethod
    def example(cls) -> "ThermalLimitSet":
        return ThermalLimitSet(limit_type="max", value=PositiveCurrent(110, "ampere"))
