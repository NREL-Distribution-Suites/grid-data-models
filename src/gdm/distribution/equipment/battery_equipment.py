"""This module contains solar equipment. """

from typing import Annotated

from infrasys import Component
from pydantic import Field

from gdm.quantities import PositiveActivePower, PositiveEnergyDC
from gdm.constants import PINT_SCHEMA


class BatteryEquipment(Component):
    """Interface for Solar Model."""

    rated_energy: Annotated[
        PositiveEnergyDC,
        PINT_SCHEMA,
        Field(..., description="Rated energy DC capacity of the battery."),
    ]

    rated_power: Annotated[
        PositiveActivePower,
        PINT_SCHEMA,
        Field(..., description="Rated power of the battery"),
    ]

    charging_efficiency: Annotated[
        float,
        Field(..., ge=0, le=100, description="Charging efficiency of the battery."),
    ]

    discharging_efficiency: Annotated[
        float,
        Field(..., ge=0, le=100, description="Discharging efficiency of the battery."),
    ]

    idling_efficiency: Annotated[
        float,
        Field(..., ge=0, le=100, description="Idling efficiency of the battery."),
    ]

    @classmethod
    def example(cls) -> "BatteryEquipment":
        "Example for a battery Equipment"
        return BatteryEquipment(
            name="battery-install1",
            rated_energy=PositiveEnergyDC(4000, "kWh"),
            rated_power=PositiveActivePower(1000, "kW"),
            charging_efficiency=98,
            discharging_efficiency=98,
            idling_efficiency=99,
        )
