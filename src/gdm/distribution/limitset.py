""" This module contains interface for operation limit sets. """

from typing import Annotated
from infrasys.component_models import Component

from gdm.quantities import PositiveCurrent, PositiveVoltage
from gdm.distribution.distribution_enum import LimitType
from pydantic import Field


class VoltageLimitSet(Component):
    """Interface for voltage limit set."""

    limit_type: Annotated[LimitType, Field(..., description="Limit type used.")]
    value: Annotated[PositiveVoltage, Field(..., description="Voltage threshold.")]

    @classmethod
    def example(cls) -> "VoltageLimitSet":
        """Example for voltage limit set."""
        return VoltageLimitSet(limit_type=LimitType.MIN, value=PositiveVoltage(400 * 0.9, "volt"))


class ThermalLimitSet(Component):
    """Interface for voltage limit set."""

    limit_type: Annotated[LimitType, Field(..., description="Limit type used.")]
    value: Annotated[PositiveCurrent, Field(..., description="Current threshold.")]

    @classmethod
    def example(cls) -> "ThermalLimitSet":
        """Example for thermal limit set."""
        return ThermalLimitSet(limit_type=LimitType.MAX, value=PositiveCurrent(110, "ampere"))
