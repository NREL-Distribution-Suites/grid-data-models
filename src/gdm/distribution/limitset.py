""" This module contains interface for operation limit sets. """

from infrasys.component_models import Component

from gdm.quantities import PositiveCurrent, PositiveVoltage
from gdm.distribution.distribution_enum import LimitType


class VoltageLimitSet(Component):
    """Interface for voltage limit set."""

    limit_type: LimitType
    value: PositiveVoltage

    @classmethod
    def example(cls) -> "VoltageLimitSet":
        """Example for voltage limit set."""
        return VoltageLimitSet(limit_type=LimitType.MIN, value=PositiveVoltage(400 * 0.9, "volt"))


class ThermalLimitSet(Component):
    """Interface for voltage limit set."""

    limit_type: LimitType
    value: PositiveCurrent

    @classmethod
    def example(cls) -> "ThermalLimitSet":
        """Example for thermal limit set."""
        return ThermalLimitSet(limit_type=LimitType.MAX, value=PositiveCurrent(110, "ampere"))
