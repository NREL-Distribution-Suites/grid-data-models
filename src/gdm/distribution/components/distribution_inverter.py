from typing import Annotated

from pydantic import Field

from gdm.distribution.equipment.inverter_equipment import InverterEquipment
from gdm.distribution.components.base.distribution_component_base import (
    DistributionComponentBase,
)
from gdm.distribution.controllers.distribution_inverter_controller import (
    PowerfactorInverterController,
)
from gdm.distribution.controllers.base.inverter_controller_base import (
    InverterControllerBase,
)


class DistributionInverter(DistributionComponentBase):
    controller: Annotated[
        InverterControllerBase,
        Field(
            PowerfactorInverterController.example(),
            description="The controller which is used for the PV array.",
        ),
    ]
    equipment: Annotated[
        InverterEquipment, Field(..., description="Inverter equipment for this controller.")
    ]

    @classmethod
    def example(cls) -> "DistributionInverter":
        """Example of a Distribution Inverter with a predefined controller and equipment."""

        return DistributionInverter(
            name="inverter1",
            controller=PowerfactorInverterController.example(),
            equipment=InverterEquipment.example(),
        )
