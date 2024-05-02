""" This module contains interface for distribution system capacitor."""

from typing import Annotated

from pydantic import Field

from gdm.quantities import PositiveVoltage
from gdm.distribution.distribution_enum import Phase
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.components.distribution_component import DistributionComponent
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.controllers.distribution_inverter_controller import (
    InverterController,
    VoltVarInverterController,
)
from gdm.distribution.equipment.solar_equipment import SolarEquipment


class DistributionSolar(DistributionComponent):
    """Interface for Solar PV system in distribution system models."""

    bus: Annotated[
        DistributionBus,
        Field(
            ...,
            description="Distribution bus to which this solar array is connected to.",
        ),
    ]
    phases: Annotated[
        list[Phase],
        Field(
            ...,
            description=(
                "List of phases at which this solar array is connected to in the same order."
            ),
        ),
    ]
    controller: Annotated[
        InverterController,
        Field(
            ...,
            description="The controller which is used for the PV array.",
        ),
    ]

    equipment: Annotated[SolarEquipment, Field(..., description="Solar PV model.")]

    @classmethod
    def example(cls) -> "DistributionSolar":
        """Example for a Solar PV"""
        return DistributionSolar(
            name="pv1",
            bus=DistributionBus(
                voltage_type="line-to-ground",
                name="Solar-DistBus1",
                nominal_voltage=PositiveVoltage(400, "volt"),
                phases=[Phase.A, Phase.B, Phase.C],
                substation=DistributionSubstation.example(),
                feeder=DistributionFeeder.example(),
            ),
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            phases=[Phase.A, Phase.B, Phase.C],
            equipment=SolarEquipment.example(),
            controller=VoltVarInverterController.example(),
        )
