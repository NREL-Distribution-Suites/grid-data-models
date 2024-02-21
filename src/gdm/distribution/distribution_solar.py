""" This module contains interface for distribution system capacitor."""

from typing import Annotated

from infrasys.component_models import ComponentWithQuantities
from pydantic import Field

from gdm.quantities import PositiveVoltage, PositiveActivePower
from gdm.distribution.distribution_enum import Phase
from gdm.distribution.distribution_common import BELONG_TO_TYPE
from gdm.distribution.distribution_bus import DistributionBus
from gdm.distribution.distribution_controller import SolarController, VoltVarSolarController

# TODO: Is a SolarEquipment necessary? Currently using the same paradigm as loads and capacitors, but with no PhaseSolarEquipment objects.
class SolarEquipment(ComponentWithQuantities):
    """Interface for Solar Model."""

    rated_capacity: Annotated[
        PositiveActivePower,
        Field(..., description="Active power rating of the Solar PV array.")
    ]

    resistance: Annotated[
        float,
        Field(..., strict=True, ge=0, le=100, description="Percentage internal resistance for the PV array."),
    ]

    reactance: Annotated[
        float,
        Field(..., strict=True, ge=0, le=100, description="Percentage internal reactance for the PV array."),
    ]

    @classmethod
    def example(cls) -> "SolarEquipment":
        "Example for a solar Equipment"
        return SolarEquipment(
            name="solar-install1",
            rated_capacity=PositiveActivePower(4, "kW"),
            resistance = 50,
            reactance = 0,
        )

class DistributionSolar(ComponentWithQuantities):
    """Interface for Solar PV system in distribution system models."""

    bus: Annotated[
        DistributionBus,
        Field(
            ...,
            description="Distribution bus to which this solar array is connected to.",
        ),
    ]
    belongs_to: BELONG_TO_TYPE
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
        SolarController,
        Field(
            ...,
            description=(
                "The controller which is used for the PV array.",
            ),
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
                name="Bus1",
                nominal_voltage=PositiveVoltage(400, "volt"),
                phases=[Phase.A, Phase.B, Phase.C],
            ),
            phases=[Phase.A, Phase.B, Phase.C],
            equipment=SolarEquipment.example(),
            controller = VoltVarSolarController.example()
        )


