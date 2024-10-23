""" This module contains interface for distribution system capacitor."""

from collections import defaultdict
from typing import Annotated

from pydantic import Field, model_validator

from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.equipment.capacitor_equipment import CapacitorEquipment
from gdm.distribution.components.base.distribution_component_base import DistributionComponentBase
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.equipment.phase_capacitor_equipment import PhaseCapacitorEquipment
from gdm.quantities import PositiveVoltage
from gdm.distribution.distribution_enum import Phase
from gdm.distribution.controllers.distribution_capacitor_controller import (
    VoltageCapacitorController,
)
from gdm.distribution.controllers.base.capacitor_controller_base import CapacitorControllerBase


class DistributionCapacitor(DistributionComponentBase):
    """Interface for capacitor present in distribution system models."""

    bus: Annotated[
        DistributionBus,
        Field(
            ...,
            description="Distribution bus to which this capacitor is connected to.",
        ),
    ]
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
        list[CapacitorControllerBase],
        Field(
            [],
            description="List of the controllers which are used for each phase in order.",
        ),
    ]

    equipment: Annotated[CapacitorEquipment, Field(..., description="Capacitor model.")]

    @classmethod
    def aggregate(
        cls,
        instances: list["DistributionCapacitor"],
        bus: DistributionBus,
        name: str,
        split_phase_mapping: dict[str, set[Phase]],
    ) -> "DistributionCapacitor":
        phase_caps = defaultdict(list)
        for cap in instances:
            if {Phase.S1, Phase.S2} & set(cap.phases):
                parent_phase = split_phase_mapping[cap.uuid]
                split_cap = PhaseCapacitorEquipment.split(
                    PhaseCapacitorEquipment.aggregate(cap.equipment.phase_capacitors, name=""),
                    len(parent_phase),
                )
                for phase in parent_phase:
                    phase_caps[phase].append(split_cap)
                continue
            for phase, phase_load in zip(cap.phases, cap.equipment.phase_capacitors):
                phase_caps[phase].append(phase_load)

        return DistributionCapacitor(
            name=name,
            bus=bus,
            phases=list(phase_caps.keys()),
            equipment=CapacitorEquipment(
                name=f"{name}_capacitor_equipment",
                phase_capacitors=[
                    PhaseCapacitorEquipment.aggregate(caps, name="")
                    for caps in phase_caps.values()
                ],
                connection_type=set([item.equipment.connection_type for item in instances]).pop(),
            ),
        )

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
                name="Capacitor-DistBus1",
                nominal_voltage=PositiveVoltage(400, "volt"),
                phases=[Phase.A, Phase.B, Phase.C],
                substation=DistributionSubstation.example(),
                feeder=DistributionFeeder.example(),
            ),
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            phases=[Phase.A, Phase.B, Phase.C],
            equipment=CapacitorEquipment.example(),
            controllers=[
                VoltageCapacitorController.example(),
                VoltageCapacitorController.example(),
                VoltageCapacitorController.example(),
            ],
        )
