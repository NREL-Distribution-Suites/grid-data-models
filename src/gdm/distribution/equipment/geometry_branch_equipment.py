""" This module contains geometry branch equipment."""

from typing import Annotated

from pydantic import Field, model_validator
from infrasys.component_models import ComponentWithQuantities

from gdm.distribution.equipment.bare_conductor_equipment import BareConductorEquipment
from gdm.distribution.equipment.concentric_cable_equipment import ConcentricCableEquipment
from gdm.quantities import Distance


class GeometryBranchEquipment(ComponentWithQuantities):
    """Interface for geometry branch info."""

    conductors: Annotated[
        list[BareConductorEquipment | ConcentricCableEquipment],
        Field(..., description="List of overhead wires or cables."),
    ]
    horizontal_positions: Annotated[
        list[Distance],
        Field(..., description="Horizontal position of the conductor."),
    ]
    vertical_positions: Annotated[
        list[Distance],
        Field(
            ...,
            description="""Vertical position of the conductor.""",
        ),
    ]

    @model_validator(mode="after")
    def validate_fields(self) -> "GeometryBranchEquipment":
        """Custom validator for geometry branch model fields."""
        if not self.conductors:
            msg = f"Number of wires must be at least 1 {self.conductors=}"
            raise ValueError(msg)

        if len(self.horizontal_positions) != len(self.conductors):
            msg = f"{self.horizontal_positions} and {self.conductors=} must be equal in length."
            raise ValueError(msg)

        if len(self.vertical_positions) != len(self.conductors):
            msg = f"{self.vertical_positions} and {self.conductors=} must be equal in length."
            raise ValueError(msg)

        return self

    @classmethod
    def example(cls) -> "GeometryBranchEquipment":
        """Example for geometry branch equipment."""
        return GeometryBranchEquipment(
            name="geometry-branch-1",
            conductors=[BareConductorEquipment.example()] * 3,
            horizontal_positions=[Distance(0, "m")] * 3,
            vertical_positions=[Distance(5.6, "m"), Distance(6.0, "m"), Distance(6.4, "m")],
        )
