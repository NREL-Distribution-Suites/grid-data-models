""" This module contains interface for Distribution Bus."""

from typing import Annotated

from infrasys.location import Location
from pydantic import Field

from gdm.distribution.distribution_enum import LimitType, Phase, VoltageTypes
from gdm.distribution.distribution_component import DistributionComponent
from gdm.distribution.distribution_common import BELONG_TO_TYPE
from gdm.distribution.limitset import VoltageLimitSet
from gdm.quantities import PositiveVoltage
from gdm.bus import PowerSystemBus


class DistributionBus(PowerSystemBus):
    """Interface for distribution bus.

    Examples:
        >>> from gdm import DistributionBus
        >>> DistributionBus.example()
    """

    voltage_type: VoltageTypes
    belongs_to: BELONG_TO_TYPE
    phases: Annotated[list[Phase], Field(..., description="List of phases for this bus.")]
    voltagelimit: Annotated[
        list[VoltageLimitSet],
        Field([], description="List of voltage limit sets for this bus."),
    ]

    @classmethod
    def example(cls) -> "DistributionBus":
        return DistributionBus(
            voltage_type=VoltageTypes.LINE_TO_LINE,
            belongs_to=DistributionComponent(substation="Dist Substation", feeder="Dist feeder"),
            phases=[Phase.A, Phase.B, Phase.C],
            nominal_voltage=PositiveVoltage(400, "volt"),
            name="DistBus1",
            voltagelimit=[
                VoltageLimitSet(
                    limit_type=LimitType.MIN, value=PositiveVoltage(400 * 0.9, "volt")
                ),
                VoltageLimitSet(
                    limit_type=LimitType.MAX, value=PositiveVoltage(400 * 1.1, "volt")
                ),
            ],
            coordinate=Location(x=20.0, y=30.0),
        )
