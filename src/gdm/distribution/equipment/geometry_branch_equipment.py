""" This module contains geometry branch equipment."""

from typing import Annotated
from itertools import groupby

from pydantic import Field, model_validator
from infrasys.component_models import ComponentWithQuantities

from gdm.distribution.equipment.bare_conductor_equipment import BareConductorEquipment
from gdm.distribution.equipment.concentric_cable_equipment import ConcentricCableEquipment
from gdm.distribution.sequence_pair import SequencePair
from gdm.quantities import Distance


class GeometryBranchEquipment(ComponentWithQuantities):
    """Interface for geometry branch info."""

    conductors: Annotated[
        list[BareConductorEquipment | ConcentricCableEquipment],
        Field(..., description="List of overhead wires or cables."),
    ]
    spacing_sequences: Annotated[
        list[SequencePair],
        Field(
            ...,
            description="""List of pair
            of sequence numbers for coupling """,
        ),
    ]
    horizontal_spacings: Annotated[
        list[Distance],
        Field(..., description="Horizontal spacing for each spacing sequences."),
    ]
    heights: Annotated[
        list[Distance],
        Field(
            ...,
            description="""Heights of each conductor from ground, positive
            for overhead and negative for underground.""",
        ),
    ]

    @model_validator(mode="after")
    def validate_fields(self) -> "GeometryBranchEquipment":
        """Custom validator for geometry branch model fields."""
        if not self.conductors:
            msg = f"Number of wires must be at least 1 {self.conductors=}"
            raise ValueError(msg)

        if len(self.spacing_sequences) != (len(self.conductors) - 1):
            msg = (
                f"Number of spacings {self.spacing_sequences} must be one "
                f"less tha number of wires {self.conductors=}."
            )
            raise ValueError(msg)

        for item in self.spacing_sequences:
            if item.from_index == item.to_index:
                msg = (
                    f"From index {item.from_index=} should not be equal "
                    f"to index {item.to_index}in spacing sequences."
                )
                raise ValueError(msg)
            if item.from_index >= len(self.conductors) or item.to_index >= len(self.conductors):
                msg = (
                    f"Sequence index {item=} can not be greater than or equal to"
                    f"length of conductors {len(self.conductors)}"
                )
                raise ValueError(msg)

        if len(list(groupby([set(item) for item in self.spacing_sequences]))) != len(
            self.spacing_sequences
        ):
            msg = f"Invalid sequence numbers in spacing sequences. {self.spacing_sequences=}"
            raise ValueError(msg)

        return self

    @classmethod
    def example(cls) -> "GeometryBranchEquipment":
        """Example for geometry branch equipment."""
        return GeometryBranchEquipment(
            name="geometry-branch-1",
            conductors=[BareConductorEquipment.example()] * 3,
            spacing_sequences=[SequencePair(0, 1), SequencePair(1, 2)],
            horizontal_spacings=[Distance(0, "m")] * 2,
            heights=[Distance(5.6, "m"), Distance(6.0, "m"), Distance(6.4, "m")],
        )
