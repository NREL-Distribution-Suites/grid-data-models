"""This module contains matrix impedance branch equipment."""

from typing import Annotated

from infrasys import Component
from pydantic import Field, model_validator

from gdm.quantities import (
    ResistancePULength,
    ReactancePULength,
    CapacitancePULength,
    PositiveCurrent,
)

from gdm.constants import PINT_SCHEMA


class MatrixImpedanceBranchEquipmentBase(Component):
    """Data model for impedance based branch."""

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

    @model_validator(mode="after")
    def validate_fields(self) -> "MatrixImpedanceBranchEquipmentBase":
        """Custom validator for fields."""
        if self.r_matrix.shape == self.x_matrix.shape == self.c_matrix.shape:
            return self

        msg = f"matrix sizes are not equals {self.r_matrix=} {self.x_matrix=} {self.c_matrix=}"
        raise ValueError(msg)
