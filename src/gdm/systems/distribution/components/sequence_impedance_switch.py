"""Three-phase distribution switch represented by sequence impedance."""

from typing import Annotated

from pydantic import Field, model_validator

from gdm.systems.distribution.components.base.distribution_switch_base import (
    DistributionSwitchBase,
)
from gdm.systems.distribution.components.base.distribution_branch_base import (
    DistributionBranchBase,
)
from gdm.systems.distribution.components.sequence_impedance_branch import SequenceImpedanceBranch
from gdm.systems.distribution.equipment.sequence_impedance_switch_equipment import (
    SequenceImpedanceSwitchEquipment,
)
from gdm.systems.distribution.enums import Phase


class SequenceImpedanceSwitch(DistributionSwitchBase):
    equipment: Annotated[
        SequenceImpedanceSwitchEquipment, Field(description="Sequence impedance switch equipment.")
    ]

    @model_validator(mode="after")
    def validate_fields(self) -> "SequenceImpedanceSwitch":
        DistributionBranchBase.validate_fields_base(self)
        if set(self.phases) != {Phase.A, Phase.B, Phase.C}:
            raise ValueError("Sequence impedance switches require phases A, B, and C.")
        return self

    @classmethod
    def example(cls) -> "SequenceImpedanceSwitch":
        branch = SequenceImpedanceBranch.example()
        return cls(
            name="sequence-switch",
            buses=branch.buses,
            phases=branch.phases,
            length=branch.length,
            is_closed=[True, True, True],
            equipment=SequenceImpedanceSwitchEquipment.example(),
        )
