"""This module contains sequence impedance branch equipment."""

from typing import Annotated
from abc import ABC

from infrasys import Component
from pydantic import Field
import numpy as np

from gdm.quantities import (
    Current,
    ResistancePULength,
    ReactancePULength,
    CapacitancePULength,
)
from gdm.constants import PINT_SCHEMA
from gdm.systems.distribution.equipment.matrix_impedance_branch_equipment import (
    MatrixImpedanceBranchEquipment,
)


class SequenceImpedanceBranchEquipmentBase(Component, ABC):
    """Sequence quantities for a reciprocal branch with equal positive/negative sequences."""

    pos_seq_resistance: Annotated[
        ResistancePULength,
        PINT_SCHEMA,
        Field(..., description="Per unit length positive sequence resistance."),
    ]
    zero_seq_resistance: Annotated[
        ResistancePULength,
        PINT_SCHEMA,
        Field(..., description="Per unit length zero sequence impedance."),
    ]
    pos_seq_reactance: Annotated[
        ReactancePULength,
        PINT_SCHEMA,
        Field(..., description="Per unit length positive sequence impedance."),
    ]
    zero_seq_reactance: Annotated[
        ReactancePULength,
        PINT_SCHEMA,
        Field(..., description="Per unit length zero sequence impedance."),
    ]
    pos_seq_capacitance: Annotated[
        CapacitancePULength,
        PINT_SCHEMA,
        Field(..., description="Per unit length positive sequence capacitance."),
    ]
    zero_seq_capacitance: Annotated[
        CapacitancePULength,
        PINT_SCHEMA,
        Field(..., description="Per unit length zero sequence capacitance."),
    ]
    ampacity: Annotated[
        Current, PINT_SCHEMA, Field(..., description="Ampacity of the conductor.", gt=0)
    ]

    def to_matrix_equipment(self) -> MatrixImpedanceBranchEquipment:
        """Return the equivalent three-phase ABC matrix without storing duplicate data."""

        def matrix(
            positive: ResistancePULength | ReactancePULength | CapacitancePULength,
            zero: ResistancePULength | ReactancePULength | CapacitancePULength,
        ) -> np.ndarray:
            mutual = (zero.to(positive.units).magnitude - positive.magnitude) / 3
            return np.full((3, 3), mutual) + np.eye(3) * positive.magnitude

        return MatrixImpedanceBranchEquipment(
            name=self.name,
            r_matrix=ResistancePULength(
                matrix(self.pos_seq_resistance, self.zero_seq_resistance),
                self.pos_seq_resistance.units,
            ),
            x_matrix=ReactancePULength(
                matrix(self.pos_seq_reactance, self.zero_seq_reactance),
                self.pos_seq_reactance.units,
            ),
            c_matrix=CapacitancePULength(
                matrix(self.pos_seq_capacitance, self.zero_seq_capacitance),
                self.pos_seq_capacitance.units,
            ),
            ampacity=self.ampacity,
        )
