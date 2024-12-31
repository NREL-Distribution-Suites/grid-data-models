"""This module contains interface for distribution substation."""

from typing import Annotated

from pydantic import Field

from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.distribution_enum import Phase
from gdm.distribution.components.base.distribution_component_base import (
    InServiceDistributionComponentBase,
)
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.equipment.voltagesource_equipment import VoltageSourceEquipment


class DistributionVoltageSource(InServiceDistributionComponentBase):
    """Interface for distribution substation."""

    bus: Annotated[
        DistributionBus,
        Field(
            ...,
            description="Distribution bus to which this voltage source is connected to.",
        ),
    ]
    phases: Annotated[list[Phase], Field(..., description="Phase to which this is connected to.")]
    equipment: Annotated[VoltageSourceEquipment, Field(..., description="Voltage source model.")]

    @classmethod
    def example(cls) -> "DistributionVoltageSource":
        """Example for distribution voltage source."""
        return DistributionVoltageSource(
            name="DistributionVoltageSource1",
            bus=DistributionBus.example(),
            phases=[Phase.A, Phase.B, Phase.C],
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            equipment=VoltageSourceEquipment.example(),
        )
