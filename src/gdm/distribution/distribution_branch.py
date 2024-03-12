""" Interface for power system branch. """

from typing import Annotated, Any, Optional
from itertools import groupby, product

from pydantic import PlainSerializer, model_validator, Field
from infrasys.component_models import Component, ComponentWithQuantities
from infrasys.quantities import Distance
from infrasys.models import InfraSysBaseModel

from gdm.distribution.distribution_wires import (
    BareConductorEquipment,
    ConcentricCableEquipment,
)
from gdm.distribution.distribution_common import BELONG_TO_TYPE
from gdm.distribution.sequence_pair import SequencePair
from gdm.distribution.distribution_bus import DistributionBus
from gdm.distribution.limitset import ThermalLimitSet
from gdm.distribution.distribution_enum import Phase
from gdm.quantities import (
    PositiveResistancePULength,
    CapacitancePULength,
    ResistancePULength,
    ReactancePULength,
    PositiveDistance,
    PositiveCurrent,
    PositiveVoltage,
)


def _get_mat_size(mat: list[list[Any]]) -> tuple[int, int]:
    """Internal function to get matrix size."""
    mat_item_sizes = set(len(item) for item in mat)
    if len(mat_item_sizes) != 1:
        msg = f"Matrix has uneven items {mat=}"
        raise ValueError(msg)
    return (len(mat), mat_item_sizes.pop())


class MatrixType(InfraSysBaseModel):
    """Interface to serialized matrix type."""

    data: Annotated[
        list[list[float]],
        Field(..., description="List of list of floats."),
    ]
    el_type: str
    unit: str


def serializer(dtype: str) -> PlainSerializer:
    """Custom serializer for pint quantity."""
    return PlainSerializer(
        lambda x: MatrixType(
            data=[[float(el.magnitude) for el in arr] for arr in x],
            el_type=dtype,
            unit=str(x[0][0].units),
        ).model_dump(),
        when_used="always",
    )


class SequenceImpedanceBranchEquipment(Component):
    """Interface for sequence impedance branch."""

    pos_seq_resistance: Annotated[
        ResistancePULength,
        Field(..., description="Per unit length positive sequence resistance."),
    ]
    zero_seq_resistance: Annotated[
        ResistancePULength,
        Field(..., description="Per unit length zero sequence impedance."),
    ]
    pos_seq_reactance: Annotated[
        ReactancePULength,
        Field(..., description="Per unit length positive sequence impedance."),
    ]
    zero_seq_reactance: Annotated[
        ReactancePULength,
        Field(..., description="Per unit length zero sequence impedance."),
    ]
    pos_seq_capacitance: Annotated[
        CapacitancePULength,
        Field(..., description="Per unit length positive sequence capacitance."),
    ]
    zero_seq_capacitance: Annotated[
        CapacitancePULength,
        Field(..., description="Per unit length zero sequence capacitance."),
    ]
    ampacity: Annotated[PositiveCurrent, Field(..., description="Ampacity of the conductor.")]
    loading_limit: Annotated[
        Optional[ThermalLimitSet],
        Field(None, description="Loading limit set for this conductor."),
    ]

    @classmethod
    def example(cls) -> "SequenceImpedanceBranchEquipment":
        """Example for sequence impedance branch model."""
        return SequenceImpedanceBranchEquipment(
            pos_seq_resistance=ResistancePULength(0.304, "ohm/mi"),
            zero_seq_resistance=ResistancePULength(0.45, "ohm/mi"),
            pos_seq_reactance=ReactancePULength(0.4, "ohm/mi"),
            zero_seq_reactance=ReactancePULength(0.4, "ohm/mi"),
            pos_seq_capacitance=CapacitancePULength(900, "nanofarad/mi"),
            zero_seq_capacitance=CapacitancePULength(700, "nanofarad/mi"),
            ampacity=PositiveCurrent(90, "ampere"),
        )


class MatrixImpedanceBranchEquipment(Component):
    """Interface for impedance based conductor."""

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
        r_matrix_size = _get_mat_size(self.r_matrix)
        x_matrix_size = _get_mat_size(self.x_matrix)
        c_matrix_size = _get_mat_size(self.c_matrix)
        if r_matrix_size == x_matrix_size == c_matrix_size:
            return self

        msg = f"matrix sizes are not equals {r_matrix_size=} {x_matrix_size=} {c_matrix_size=}"
        raise ValueError(msg)

    @classmethod
    def example(cls) -> "MatrixImpedanceBranchEquipment":
        """Example for matrix impedance model."""
        return MatrixImpedanceBranchEquipment(
            r_matrix=PositiveResistancePULength([[1,2,3] for _ in range(3)] ,  "ohm/mi"),
            x_matrix=ReactancePULength([[1,2,3] for _ in range(3)] ,  "ohm/mi"),
            c_matrix=CapacitancePULength([[1,2,3] for _ in range(3)] ,  "farad/mi"),
            ampacity=PositiveCurrent(90, "ampere"),
        )

class GeometryBranchEquipment(Component):
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
            conductors=[BareConductorEquipment.example()] * 3,
            spacing_sequences=[SequencePair(0, 1), SequencePair(1, 2)],
            horizontal_spacings=[Distance(0, "m")] * 2,
            heights=[Distance(5.6, "m"), Distance(6.0, "m"), Distance(6.4, "m")],
        )


class DistributionBranch(ComponentWithQuantities):
    """Interface for distribution branch."""

    belongs_to: BELONG_TO_TYPE
    buses: Annotated[
        list[DistributionBus],
        Field(..., description="List of buses connecting a branch."),
    ]
    length: Annotated[PositiveDistance, Field(..., description="Length of the branch.")]
    phases: Annotated[
        list[Phase],
        Field(..., description="List of phases in the same order as conductors."),
    ]
    is_closed: Annotated[bool, Field(True, description="Status of the line.")]

    @model_validator(mode="after")
    def validate_fields(self) -> "DistributionBranch":
        """Custom validator for base distribution branch."""
        if len(self.buses) != 2:
            msg = f"Number of buses {len(self.buses)} must be 2."
            raise ValueError(msg)

        for phase, bus in product(self.phases, self.buses):
            if phase not in bus.phases:
                msg = f"Conductor phase ({phase=}) does not match bus phases ({bus.phases=})"
                raise ValueError(msg)

        if self.buses[0].name == self.buses[1].name:
            msg = (
                f"From bus {self.buses[0].name=} and to bus"
                f"{self.buses[1].name=} should be different."
            )
            raise ValueError(msg)

        if self.buses[0].nominal_voltage != self.buses[1].nominal_voltage:
            msg = (
                f"From bus {self.buses[0].nominal_voltage=}"
                f"and to bus voltage {self.buses[1].nominal_voltage=} rating should be same."
            )
            raise ValueError(msg)

        if len(self.phases) != len(set(self.phases)):
            msg = f"Duplicate phases not allowed for conductors {self.phases=}"
            raise ValueError(msg)

        return self

    @classmethod
    def example(cls) -> "DistributionBranch":
        """Example for base distribution branch."""
        bus1 = DistributionBus(
            voltage_type="line-to-ground",
            phases=[Phase.A, Phase.B, Phase.C],
            nominal_voltage=PositiveVoltage(400, "volt"),
            name="DistBus1",
        )
        bus2 = DistributionBus(
            voltage_type="line-to-ground",
            phases=[Phase.A, Phase.B, Phase.C],
            nominal_voltage=PositiveVoltage(400, "volt"),
            name="DistBus2",
        )
        return DistributionBranch(
            buses=[bus1, bus2],
            length=PositiveDistance(130.2, "meter"),
            phases=[Phase.A, Phase.B, Phase.C],
            name="p14u405",
        )


class MatrixImpedanceBranch(DistributionBranch):
    """Interface for matrix impedance branch."""

    equipment: Annotated[
        MatrixImpedanceBranchEquipment,
        Field(..., description="Matrix impedance branch equipment."),
    ]

    @model_validator(mode="after")
    def validate_fields(self) -> "MatrixImpedanceBranch":
        """Custom validator for matrix impedance branch."""
        for mat in [
            self.equipment.r_matrix,
            self.equipment.x_matrix,
            self.equipment.c_matrix,
        ]:
            mat_size = _get_mat_size(mat)
            if set(mat_size).pop() != len(self.phases):
                msg = f"Length of matrix {mat=} did not match number of phases {self.phases=}"
                raise ValueError(msg)

        return self

    @classmethod
    def example(cls) -> "MatrixImpedanceBranch":
        """Example for matrix impedance branch."""
        base_branch = DistributionBranch.example()
        return MatrixImpedanceBranch(
            buses=base_branch.buses,
            length=base_branch.length,
            phases=base_branch.phases,
            is_closed=True,
            name=base_branch.name,
            equipment=MatrixImpedanceBranchEquipment.example(),
        )


class SequenceImpedanceBranch(DistributionBranch):
    """Interface for sequence impedance branch."""

    equipment: Annotated[
        SequenceImpedanceBranchEquipment, Field(..., description="Sequence impedance branch.")
    ]

    @model_validator(mode="after")
    def validate_fields(self) -> "SequenceImpedanceBranch":
        """Custom validator for sequence impedance branch."""
        if len(self.phases) == 1:
            msg = f"Sequence impedance assigned to single phase {self.phases=}"
            raise ValueError(msg)
        return self

    @classmethod
    def example(cls) -> "SequenceImpedanceBranch":
        """Example for sequence impedance branch."""
        base_branch = DistributionBranch.example()
        return SequenceImpedanceBranch(
            buses=base_branch.buses,
            length=base_branch.length,
            phases=base_branch.phases,
            is_closed=True,
            name=base_branch.name,
            equipment=SequenceImpedanceBranchEquipment.example(),
        )


class GeometryBranch(DistributionBranch):
    """Interface for geometry based lines."""

    equipment: Annotated[
        GeometryBranchEquipment, Field(..., description="Geometry branch equipment.")
    ]

    def validate_fields(self) -> "GeometryBranch":
        """Custom validator for geometry branch fields."""
        if len(self.phases) != len(self.equipment.conductors):
            msg = "Number of phases is not equal to number of wires."
            raise ValueError(msg)
        return self

    @classmethod
    def example(cls) -> "GeometryBranch":
        """Example for geometry branch."""
        base_branch = DistributionBranch.example()
        return GeometryBranch(
            buses=base_branch.buses,
            length=base_branch.length,
            phases=base_branch.phases,
            is_closed=True,
            name=base_branch.name,
            equipment=GeometryBranchEquipment.example(),
        )
