""" This module contains matrix impedacne phase."""

from typing import Annotated

from pydantic import Field
from infrasys.quantities import Time


from gdm.distribution.equipment.matrix_impedance_branch_equipment import (
    MatrixImpedanceBranchEquipment,
)
from gdm.distribution.curve import Curve


class MatrixImpedanceFuseEquipment(MatrixImpedanceBranchEquipment):
    """Interface for impedance based fuse equipment."""

    delay: Annotated[Time, Field(description="Delay time before blowing the fuse.")]
    tcc_curve: Annotated[Curve, Field(description="Time current curve")]

    @classmethod
    def example(cls) -> "MatrixImpedanceFuseEquipment":
        """Example for matrix impedance model."""
        return MatrixImpedanceFuseEquipment(
            **MatrixImpedanceBranchEquipment.example().model_dump(exclude_none=True),
            delay=Time(0, "minutes"),
            tcc_curve=Curve(curve_x=[1, 2], curve_y=[1, 2]),
        )
