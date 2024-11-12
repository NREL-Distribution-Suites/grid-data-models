""" This module contains geometry branch equipment."""

from typing import Annotated

from pydantic import Field, model_validator
from infrasys import Component

from gdm.quantities import Distance
from gdm.constants import PINT_SCHEMA


class GeometryBranchEquipment(Component):
    """Interface for geometry branch info."""

    horizontal_positions: Annotated[
        Distance,
        PINT_SCHEMA,
        Field(..., description="Horizontal position of the conductor."),
    ]
    vertical_positions: Annotated[
        Distance,
        PINT_SCHEMA,
        Field(
            ...,
            description="""Vertical position of the conductor.""",
        ),
    ]

    @model_validator(mode="after")
    def validate_fields(self) -> "GeometryBranchEquipment":
        """Custom validator for geometry branch model fields."""
        return self

    @classmethod
    def example(cls) -> "GeometryBranchEquipment":
        """Example for geometry branch equipment."""
        return GeometryBranchEquipment(
            name="geometry-branch-1",
            horizontal_positions=Distance([5.6, 6.0, 6.4], "m") * 3,
            vertical_positions=Distance([5.6, 6.0, 6.4], "m"),
        )
