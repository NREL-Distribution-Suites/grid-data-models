""" This module contains interface for Distribution Bus."""

from typing import Annotated

from infrasys import Location
from pydantic import Field

from gdm.distribution.distribution_enum import LimitType, Phase, VoltageTypes
from gdm.distribution.components.distribution_component import DistributionComponent
from gdm.distribution.distribution_common import BELONG_TO_TYPE
from gdm.distribution.limitset import VoltageLimitSet
from gdm.quantities import PositiveVoltage
from gdm.bus import PowerSystemBus


class DistributionBus(PowerSystemBus):
    """Interface for distribution bus.

    Examples
    --------
    Getting a sample DistributionBus.

    >>> from gdm import DistributionBus
    >>> DistributionBus.example()

    A single phase bus.

    >>> from gdm import Phase, VoltageTypes
    >>> from gdm.quantities import PositiveVoltage
    >>> DistributionBus(
            name="Bus-1",
            phases=[Phase.A],
            voltage_type=VoltageTypes.LINE_TO_GROUND,
            nominal_voltage=PositiveVoltage(400, "volt"),
        )

    A three phase bus.

    >>> DistributionBus(
            name="Three-Phase-Bus",
            phases=[Phase.A, Phase.B, Phase.C],
            voltage_type=VoltageTypes.LINE_TO_LINE,
            nominal_voltage=PositiveVoltage(13.2, "kilovolt"),
        )

    A bus with cartesian coordinate.

    >>> from infrasys import Location
    >>> DistributionBus(
            name="Bus-1",
            phases=[Phase.A],
            voltage_type=VoltageTypes.LINE_TO_GROUND,
            nominal_voltage=PositiveVoltage(400, "volt"),
            coordinate=Location(x=10, y=20)
        )

    A bus with "EPSG:4326" coordinate reference system coordinate.

    >>> DistributionBus(
            name="Bus-1",
            phases=[Phase.A],
            voltage_type=VoltageTypes.LINE_TO_GROUND,
            nominal_voltage=PositiveVoltage(400, "volt"),
            coordinate=Location(x=10, y=20, crs="epsg:4326")
        )

    A bus with feeder and substation. Let's say you want to create a
    bus that belongs to feeder `Feeder-1` and substation `Substation-1`.

    >>> from gdm import DistributionComponent, DistributionFeeder,
        DistributionSubstation
    >>> feeder = DistributionFeeder(name="Feeder-1")
    >>> substation = DistributionSubstation(
            name="Substation-1",
            feeders=[DistributionFeeder(name="Feeder-1")]
        )
    >>> DistributionBus(
            name="Bus-1",
            phases=[Phase.A],
            voltage_type=VoltageTypes.LINE_TO_GROUND,
            nominal_voltage=PositiveVoltage(400, "volt"),
            belongs_to=DistributionComponent(
                feeder=feeder,
                substation=substation
            )
        )

    A bus with voltage limits.

    >>> from gdm import VoltageLimitSet
    >>> min_voltage_limit = VoltageLimitSet(
            limit_type=LimitType.MIN,
            value=PositiveVoltage(400 * 0.9, "volt")
        )
    >>> max_voltage_limit = VoltageLimitSet(
            limit_type=LimitType.MAX,
            value=PositiveVoltage(400 * 1.1, "volt")
        )
    >>> DistributionBus(
            name="Bus-1",
            phases=[Phase.A],
            voltage_type=VoltageTypes.LINE_TO_GROUND,
            nominal_voltage=PositiveVoltage(400, "volt"),
            voltagelimits=[
                min_voltage_limit,max_voltage_limit
            ]
        )

    """

    voltage_type: Annotated[VoltageTypes, Field(..., description="Voltage types for buses.")]
    belongs_to: BELONG_TO_TYPE
    phases: Annotated[list[Phase], Field(..., description="List of phases for this bus.")]
    voltagelimits: Annotated[
        list[VoltageLimitSet],
        Field([], description="List of voltage limit sets for this bus."),
    ]

    @classmethod
    def example(cls) -> "DistributionBus":
        return DistributionBus(
            voltage_type=VoltageTypes.LINE_TO_LINE,
            belongs_to=DistributionComponent.example(),
            phases=[Phase.A, Phase.B, Phase.C],
            nominal_voltage=PositiveVoltage(400, "volt"),
            name="DistBus1",
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
