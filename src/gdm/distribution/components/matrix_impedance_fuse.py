"""This module contains distribution fuse."""

from typing import Annotated

from pydantic import Field

from gdm.distribution.components.distribution_switch import DistributionSwitch
from gdm.distribution.equipment.matrix_impedance_fuse_equipment import MatrixImpedanceFuseEquipment


class MatrixImpedanceFuse(DistributionSwitch):
    """Interface for distribution fuse."""

    equipment: Annotated[
        MatrixImpedanceFuseEquipment,
        Field(..., description="Matrix impedance branch equipment."),
    ]

    @classmethod
    def example(cls) -> "MatrixImpedanceFuse":
        return MatrixImpedanceFuse(
            **DistributionSwitch.example().model_dump(exclude_none=True),
            equipment=MatrixImpedanceFuseEquipment.example(),
        )
