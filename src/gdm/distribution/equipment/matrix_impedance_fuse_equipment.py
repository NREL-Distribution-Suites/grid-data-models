""" This module contains matrix impedacne phase."""

from typing import Annotated

from pydantic import Field
from infrasys.quantities import Time


from gdm.distribution.equipment.matrix_impedance_branch_equipment import (
    MatrixImpedanceBranchEquipment,
)
from gdm.distribution.curve import TimeCurrentCurve
from gdm.constants import PINT_SCHEMA


class MatrixImpedanceFuseEquipment(MatrixImpedanceBranchEquipment):
    """Interface for impedance based fuse equipment."""

    delay: Annotated[Time, PINT_SCHEMA, Field(description="Delay time before blowing the fuse.")]
    tcc_curve: Annotated[TimeCurrentCurve, Field(description="Time current curve")]

    @classmethod
    def example(cls) -> "MatrixImpedanceFuseEquipment":
        """Example for matrix impedance model."""
        return MatrixImpedanceFuseEquipment(
            **MatrixImpedanceBranchEquipment.example().model_dump(exclude_none=True),
            delay=Time(0, "minutes"),
            tcc_curve=TimeCurrentCurve.example(),
        )
