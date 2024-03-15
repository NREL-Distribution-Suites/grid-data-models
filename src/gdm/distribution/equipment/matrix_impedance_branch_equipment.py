""" This module contains matrix impedance branch equipment."""

from typing import Annotated, Optional, Any

from infrasys.component_models import ComponentWithQuantities
from pydantic import Field, model_validator

from gdm.quantities import (
    PositiveResistancePULength,
    ReactancePULength,
    CapacitancePULength,
    PositiveCurrent,
)
from gdm.distribution.limitset import ThermalLimitSet


def get_mat_size(mat: list[list[Any]]) -> tuple[int, int]:
    """Internal function to get matrix size."""
    mat_item_sizes = set(len(item) for item in mat)
    if len(mat_item_sizes) != 1:
        msg = f"Matrix has uneven items {mat=}"
        raise ValueError(msg)
    return (len(mat), mat_item_sizes.pop())


class MatrixImpedanceBranchEquipment(ComponentWithQuantities):
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
    ampacity: Annotated[PositiveCurrent, Field(..., description="Ampacity of the conducotr.")]
    loading_limit: Annotated[
        Optional[ThermalLimitSet],
        Field(None, description="Loading limit set for this conductor."),
    ]

    @model_validator(mode="after")
    def validate_fields(self) -> "MatrixImpedanceBranchEquipment":
        """Custom validator for fields."""
        r_matrix_size = get_mat_size(self.r_matrix)
        x_matrix_size = get_mat_size(self.x_matrix)
        c_matrix_size = get_mat_size(self.c_matrix)
        if r_matrix_size == x_matrix_size == c_matrix_size:
            return self

        msg = f"matrix sizes are not equals {r_matrix_size=} {x_matrix_size=} {c_matrix_size=}"
        raise ValueError(msg)

    @classmethod
    def example(cls) -> "MatrixImpedanceBranchEquipment":
        """Example for matrix impedance model."""
        return MatrixImpedanceBranchEquipment(
            name="matrix-impedance-branch-1",
            r_matrix=PositiveResistancePULength([[1, 2, 3] for _ in range(3)], "ohm/mi"),
            x_matrix=ReactancePULength([[1, 2, 3] for _ in range(3)], "ohm/mi"),
            c_matrix=CapacitancePULength([[1, 2, 3] for _ in range(3)], "farad/mi"),
            ampacity=PositiveCurrent(90, "ampere"),
        )
