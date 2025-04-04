"""This module contains solar equipment."""

from typing import Annotated

from infrasys import Component
from pydantic import Field

from gdm.quantities import PositiveActivePower, PositiveEnergyDC, PositiveVoltage
from gdm.distribution.enums import VoltageTypes
from gdm.constants import PINT_SCHEMA


class BatteryEquipment(Component):
    """Interface for Solar Model."""

    rated_energy: Annotated[
        PositiveEnergyDC,
        PINT_SCHEMA,
        Field(..., description="Rated energy capacity (DC) of the battery."),
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
    rated_voltage: Annotated[
        PositiveVoltage,
        Field(..., description="Rated voltage for this battery equipment."),
    ]
    voltage_type: Annotated[
        VoltageTypes,
        Field(..., description="Rated voltage is line to line or line to neutral."),
    ]

    @classmethod
    def example(cls) -> "BatteryEquipment":
        "Example for a battery Equipment"
        return BatteryEquipment(
            name="battery-install1",
            rated_energy=PositiveEnergyDC(4, "kWh"),
            rated_power=PositiveActivePower(1, "kW"),
            charging_efficiency=98,
            discharging_efficiency=98,
            idling_efficiency=99,
            rated_voltage=PositiveVoltage(12.47, "kilovolt"),
            voltage_type=VoltageTypes.LINE_TO_LINE,
        )
