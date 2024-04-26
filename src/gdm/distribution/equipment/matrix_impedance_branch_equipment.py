""" This module contains matrix impedance branch equipment."""

from typing import Annotated, Optional

from infrasys import Component
from pydantic import Field, model_validator

from gdm.quantities import (
    ResistancePULength,
    ReactancePULength,
    CapacitancePULength,
    PositiveCurrent,
)
from gdm.distribution.limitset import ThermalLimitSet
from gdm.constants import PINT_SCHEMA


class MatrixImpedanceBranchEquipment(Component):
    """Interface for impedance based branch."""

    r_matrix: Annotated[
        ResistancePULength,
        PINT_SCHEMA,
        Field(..., description="Per unit length resistance matrix."),
    ]
    x_matrix: Annotated[
        ReactancePULength,
        PINT_SCHEMA,
        Field(..., description="Per unit length reactance matrix."),
    ]
    c_matrix: Annotated[
        CapacitancePULength,
        PINT_SCHEMA,
        Field(..., description="Per unit length capacitance matrix."),
    ]
    ampacity: Annotated[
        PositiveCurrent, PINT_SCHEMA, Field(..., description="Ampacity of the conducotr.")
    ]
    loading_limit: Annotated[
        Optional[ThermalLimitSet],
        Field(None, description="Loading limit set for this conductor."),
    ]

    @model_validator(mode="after")
    def validate_fields(self) -> "MatrixImpedanceBranchEquipment":
        """Custom validator for fields."""
        if self.r_matrix.shape == self.x_matrix.shape == self.c_matrix.shape:
            return self

        msg = f"matrix sizes are not equals {self.r_matrix=} {self.x_matrix=} {self.c_matrix=}"
        raise ValueError(msg)

    @classmethod
    def example(cls) -> "MatrixImpedanceBranchEquipment":
        """Example for matrix impedance model."""
        return MatrixImpedanceBranchEquipment(
            name="matrix-impedance-branch-1",
            r_matrix=ResistancePULength([[1, 2, 3] for _ in range(3)], "ohm/mi"),
            x_matrix=ReactancePULength([[1, 2, 3] for _ in range(3)], "ohm/mi"),
            c_matrix=CapacitancePULength([[1, 2, 3] for _ in range(3)], "farad/mi"),
            ampacity=PositiveCurrent(90, "ampere"),
        )
