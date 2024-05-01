""" This module contains matrix impedance branch equipment."""

from typing import Annotated, Optional

from infrasys import Component
from pydantic import Field, model_validator

from gdm.quantities import (
    PositiveResistancePULength,
    ReactancePULength,
    CapacitancePULength,
    PositiveCurrent,
)
from gdm.distribution.limitset import ThermalLimitSet


class MatrixImpedanceBranchEquipment(Component):
    """Interface for impedance based branch."""

    r_matrix: Annotated[
        PositiveResistancePULength,
        Field(..., description="Per unit length resistance matrix."),
    ]
    x_matrix: Annotated[
        ReactancePULength,
        Field(..., description="Per unit length reactance matrix."),
    ]
    c_matrix: Annotated[
        CapacitancePULength,
        Field(..., description="Per unit length capacitance matrix."),
    ]
    ampacity: Annotated[PositiveCurrent, Field(..., description="Ampacity of the conductor.")]
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
            r_matrix=PositiveResistancePULength([[0.08820, 0.0312137, 0.0306264], [0.0312137, 0.0901946, 0.0316143 ], [0.0306264, 0.0316143, 0.0889665]], "ohm/mi"),
            x_matrix=ReactancePULength([[0.20744, 0.0935314, 0.0760312], [0.0935314, 0.200783, 0.0855879], [0.0760312, 0.0855879, 0.204877]], "ohm/mi"),
            c_matrix=CapacitancePULength([[2.90301, -0.679335, -0.22313], [-0.679335, 3.15896, -0.481416], [-0.22313, -0.481416, 2.8965]], "nanofarad/mi"),
            ampacity=PositiveCurrent(90, "ampere"),
        )
