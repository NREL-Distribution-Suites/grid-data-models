""" This module contains interface for distribution system capacitor."""

from typing import Annotated

from infrasys.component_models import Component, ComponentWithQuantities
from pydantic import Field, model_validator

from gdm.quantities import PositiveReactance, PositiveResistance, PositiveVoltage
from gdm.distribution.distribution_enum import ConnectionType, Phase
from gdm.distribution.distribution_common import BELONG_TO_TYPE
from gdm.distribution.distribution_bus import DistributionBus
from gdm.capacitor import PowerSystemCapacitor
from gdm.distribution.distribution_capacitor_controller import CapacitorController, VoltageCapacitorController


class PhaseCapacitorEquipment(PowerSystemCapacitor):
    """Interface for phase capacitor."""

    resistance: Annotated[
        PositiveResistance,
        Field(
            PositiveResistance(0, "ohm"),
            description="Positive resistance for the capacitor.",
        ),
    ]
    reactance: Annotated[
        PositiveReactance,
        Field(
            PositiveReactance(0, "ohm"),
            description="Positive reactance for the capacitor.",
        ),
    ]

    @classmethod
    def example(cls) -> "PhaseCapacitorEquipment":
        """Example for phase capacitor equipment."""
        base_cap = PowerSystemCapacitor.example()
        return PhaseCapacitorEquipment(
            name=base_cap.name,
            rated_capacity=base_cap.rated_capacity,
            num_banks=base_cap.num_banks,
            num_banks_on=base_cap.num_banks_on,
        )


class CapacitorEquipment(Component):
    """Interface for capacitor model."""

    phase_capacitors: Annotated[
        list[PhaseCapacitorEquipment],
        Field(
            ...,
            description="List of phase capacitors for this distribution capacitor.",
        ),
    ]
    connection_type: Annotated[
        ConnectionType,
        Field(ConnectionType.STAR, description="Connection type for this capacitor."),
    ]

    @classmethod
    def example(cls) -> "CapacitorEquipment":
        """Example for capacitor model."""
        return CapacitorEquipment(
            phase_capacitors=[PhaseCapacitorEquipment.example()] * 3,
            connection_type=ConnectionType.STAR,
        )


class DistributionCapacitor(ComponentWithQuantities):
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
            description=(
                "List of the controllers which are used for each phase in order.",
            ),
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
                VoltageCapacitorController.example()
            ],
        )
