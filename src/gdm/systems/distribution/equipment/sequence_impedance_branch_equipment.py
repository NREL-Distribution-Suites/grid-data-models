"""Sequence impedance equipment for distribution branches."""

from gdm.quantities import Current, ResistancePULength, ReactancePULength, CapacitancePULength
from gdm.systems.distribution.equipment.base.sequence_impedance_branch_equipment_base import (
    SequenceImpedanceBranchEquipmentBase,
)


class SequenceImpedanceBranchEquipment(SequenceImpedanceBranchEquipmentBase):
    @classmethod
    def example(cls) -> "SequenceImpedanceBranchEquipment":
        return cls(
            name="sequence-impedance-branch-1",
            pos_seq_resistance=ResistancePULength(0.304, "ohm/mi"),
            zero_seq_resistance=ResistancePULength(0.45, "ohm/mi"),
            pos_seq_reactance=ReactancePULength(0.4, "ohm/mi"),
            zero_seq_reactance=ReactancePULength(0.4, "ohm/mi"),
            pos_seq_capacitance=CapacitancePULength(900, "nanofarad/mi"),
            zero_seq_capacitance=CapacitancePULength(700, "nanofarad/mi"),
            ampacity=Current(90, "ampere"),
        )
