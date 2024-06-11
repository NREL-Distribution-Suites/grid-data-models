"""This module contains sequence impedance branch."""

from typing import Annotated

from pydantic import Field, model_validator

from gdm.distribution.components.base.distribution_branch_base import DistributionBranchBase
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.equipment.sequence_impedance_branch_equipment import (
    SequenceImpedanceBranchEquipment,
)
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.distribution_enum import Phase
from gdm.quantities import PositiveVoltage, PositiveDistance


class SequenceImpedanceBranch(DistributionBranchBase):
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
        bus1 = DistributionBus(
            voltage_type="line-to-ground",
            phases=[Phase.A, Phase.B, Phase.C],
            nominal_voltage=PositiveVoltage(400, "volt"),
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            name="Branch-DistBus1",
        )
        bus2 = DistributionBus(
            voltage_type="line-to-ground",
            phases=[Phase.A, Phase.B, Phase.C],
            nominal_voltage=PositiveVoltage(400, "volt"),
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            name="Branch-DistBus2",
        )
        return SequenceImpedanceBranch(
            buses=[bus1, bus2],
            length=PositiveDistance(130.2, "meter"),
            phases=[Phase.A, Phase.B, Phase.C],
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            name="DistBranch1",
            equipment=SequenceImpedanceBranchEquipment.example(),
        )
