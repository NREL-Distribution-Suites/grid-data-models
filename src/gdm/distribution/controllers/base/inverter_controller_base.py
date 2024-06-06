from typing import Annotated
from abc import ABC

from infrasys import Component
from pydantic import Field

from gdm.distribution.equipment.inverter_equipment import InverterEquipment


class InverterControllerBase(Component, ABC):
    """Interface for Inverter controllers."""

    name: Annotated[str, Field("", description="Name of the inverter controller.")]
    equipment: Annotated[
        InverterEquipment, Field(..., description="Inverter equipment for this controller.")
    ]
