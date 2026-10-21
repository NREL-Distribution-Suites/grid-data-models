"""Sequence impedance equipment for distribution switches."""

from typing import Annotated

from pydantic import Field

from gdm.systems.distribution.controllers.distribution_switch_controller import (
    DistributionSwitchController,
)
from gdm.systems.distribution.equipment.base.sequence_impedance_branch_equipment_base import (
    SequenceImpedanceBranchEquipmentBase,
)
from gdm.systems.distribution.equipment.sequence_impedance_branch_equipment import (
    SequenceImpedanceBranchEquipment,
)


class SequenceImpedanceSwitchEquipment(SequenceImpedanceBranchEquipmentBase):
    controller: Annotated[
        DistributionSwitchController | None,
        Field(None, description="Optional controller for this switch."),
    ]

    @classmethod
    def example(cls) -> "SequenceImpedanceSwitchEquipment":
        return cls(**SequenceImpedanceBranchEquipment.example().model_dump(exclude_none=True))
