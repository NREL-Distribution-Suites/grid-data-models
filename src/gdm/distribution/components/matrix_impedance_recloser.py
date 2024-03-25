"""This module contains matrix impedance recloser device."""

from typing import Annotated

from pydantic import Field

from gdm.distribution.components.distribution_switch import DistributionSwitch
from gdm.distribution.equipment.matrix_impedance_recloser_equipment import (
    MatrixImpedanceRecloserEquipment,
)
from gdm.distribution.controllers.distribution_recloser_controller import (
    DistributionRecloserController,
)


class MatrixImpedanceRecloser(DistributionSwitch):
    """Interface for distribution recloser."""

    equipment: Annotated[
        MatrixImpedanceRecloserEquipment,
        Field(..., description="Matrix impedance recloser equipment."),
    ]
    controller: Annotated[
        DistributionRecloserController, Field(..., description="Instance of recloser controller.")
    ]

    @classmethod
    def example(cls) -> "MatrixImpedanceRecloser":
        return MatrixImpedanceRecloser(
            **DistributionSwitch.example().model_dump(exclude_none=True),
            equipment=MatrixImpedanceRecloserEquipment.example(),
            controller=DistributionRecloserController.example(),
        )
