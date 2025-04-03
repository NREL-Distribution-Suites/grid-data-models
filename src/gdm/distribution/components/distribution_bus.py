""" This module contains interface for Distribution Bus."""

from typing import Annotated, Optional

from infrasys import Location
from pydantic import Field

from gdm.distribution.distribution_enum import LimitType, Phase, VoltageTypes
from gdm.distribution.components.base.distribution_component_base import DistributionComponentBase
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.limitset import VoltageLimitSet
from gdm.quantities import PositiveVoltage
from gdm.constants import PINT_SCHEMA


class DistributionBus(DistributionComponentBase):
    """Interface for distribution bus.

    Examples:
        >>> from gdm import DistributionBus
        >>> DistributionBus.example()
    """

    voltage_type: Annotated[VoltageTypes, Field(..., description="Voltage types for buses.")]
    phases: Annotated[list[Phase], Field(..., description="List of phases for this bus.")]
    voltagelimits: Annotated[
        list[VoltageLimitSet],
        Field([], description="List of voltage limit sets for this bus."),
    ]
    rated_voltage: Annotated[
        PositiveVoltage,
        PINT_SCHEMA,
        Field(..., description="rated voltage for this bus."),
    ]
    coordinate: Annotated[
        Optional[Location],
        Field(None, description="Coordinate for the power system bus."),
    ]

    @classmethod
    def example(cls) -> "DistributionBus":
        return DistributionBus(
            voltage_type=VoltageTypes.LINE_TO_LINE,
            phases=[Phase.A, Phase.B, Phase.C],
            rated_voltage=PositiveVoltage(400, "volt"),
            name="DistBus1",
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            voltagelimits=[
                VoltageLimitSet(
                    limit_type=LimitType.MIN, value=PositiveVoltage(400 * 0.9, "volt")
                ),
                VoltageLimitSet(
                    limit_type=LimitType.MAX, value=PositiveVoltage(400 * 1.1, "volt")
                ),
            ],
            coordinate=Location(x=20.0, y=30.0),
        )
