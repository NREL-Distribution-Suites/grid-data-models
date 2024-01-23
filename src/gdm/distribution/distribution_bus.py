""" This module contains interface for Distribution Bus."""
from infrasys.location import Location
from typing import Annotated, Literal, Optional

from gdm.quantities import PositiveVoltage
from pydantic import Field

from gdm.distribution.distribution_component import DistributionComponent
from gdm.distribution.limitset import VoltageLimitSet
from gdm.distribution.distribution_enum import Phase
from gdm.bus import PowerSystemBus


class DistributionBus(PowerSystemBus):
    """Interface for distribution bus.

    Examples:
        >>> from gdm import DistributionBus
        >>> DistributionBus.example()
    """

    voltage_type: Literal["line-to-line", "line-to-ground"]
    belongs_to: Annotated[
        Optional[DistributionComponent],
        Field(
            None,
            description="Provides info about substation and feeder. ",
        ),
    ]
    phases: Annotated[list[Phase], Field(..., description="List of phases for this bus.")]
    voltagelimit: Annotated[
        list[VoltageLimitSet],
        Field([], description="List of voltage limit sets for this bus."),
    ]

    @classmethod
    def example(cls) -> "DistributionBus":
        return DistributionBus(
            voltage_type="line-to-ground",
            belongs_to=DistributionComponent(substation="Dist Substation", feeder="Dist feeder"),
            phases=[Phase.A, Phase.B, Phase.C],
            nominal_voltage=PositiveVoltage(400, "volt"),
            name="DistBus1",
            voltagelimit=[
                VoltageLimitSet(limit_type="min", value=PositiveVoltage(400 * 0.9, "volt")),
                VoltageLimitSet(limit_type="max", value=PositiveVoltage(400 * 1.1, "volt")),
            ],
            coordinate=Location(x=20.0, y=30.0),
        )
