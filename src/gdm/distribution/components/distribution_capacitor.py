""" This module contains interface for distribution system capacitor."""

from typing import Annotated

from infrasys import Component
from pydantic import Field, model_validator

from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.equipment.capacitor_equipment import CapacitorEquipment
from gdm.quantities import PositiveVoltage
from gdm.distribution.distribution_enum import Phase
from gdm.distribution.distribution_common import BELONG_TO_TYPE
from gdm.distribution.controllers.distribution_capacitor_controller import (
    CapacitorController,
    VoltageCapacitorController,
)


class DistributionCapacitor(Component):
    """Interface for capacitor present in distribution system models."""

    bus: Annotated[
        DistributionBus,
        Field(
            ...,
            description="Distribution bus to which this capacitor is connected to.",
        ),
    ]
    belongs_to: BELONG_TO_TYPE
    phases: Annotated[
        list[Phase],
        Field(
            ...,
            description=(
                "List of phases at which this phase capacitors"
                "are connected to in the same order."
            ),
        ),
    ]
    controllers: Annotated[
        list[CapacitorController],
        Field(
            [],
            description="List of the controllers which are used for each phase in order.",
        ),
    ]

    equipment: Annotated[CapacitorEquipment, Field(..., description="Capacitor model.")]

    @model_validator(mode="after")
    def validate_fields(self) -> "DistributionCapacitor":
        """Custom validator for fields."""
        if not set(self.phases).issubset(set(self.bus.phases)):
            msg = (
                f"Phase capacitors phases ({self.phases}) should be subset of bus phases"
                f" ({self.bus.phases}) to which it is connected to."
            )
            raise ValueError(msg)
        if len(self.phases) != len(self.equipment.phase_capacitors):
            msg = (
                f"Length of phase capacitors {self.equipment.phase_capacitors=} "
                f"did not match length of phases {self.phases=}"
            )
        if len(self.equipment.phase_capacitors) != len(self.controllers):
            msg = (
                f"Number of controllers ({self.controllers=}) "
                f"did not match number of phase capacitors {self.equipment.phase_capacitors=}"
            )
        return self

    @classmethod
    def example(cls) -> "DistributionCapacitor":
        """Example for distribution capacitor."""
        return DistributionCapacitor(
            name="Capacitor1",
            bus=DistributionBus(
                voltage_type="line-to-ground",
                name="Bus1",
                nominal_voltage=PositiveVoltage(400, "volt"),
                phases=[Phase.A, Phase.B, Phase.C],
            ),
            phases=[Phase.A, Phase.B, Phase.C],
            equipment=CapacitorEquipment.example(),
            controllers=[
                VoltageCapacitorController.example(),
                VoltageCapacitorController.example(),
                VoltageCapacitorController.example(),
            ],
        )
