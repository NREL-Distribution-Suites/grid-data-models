"""This module contains geometry branch."""

from typing import Annotated

from pydantic import Field

from gdm.distribution.components.base.distribution_branch_base import (
    DistributionBranchBase,
)
from gdm.distribution.equipment.geometry_branch_equipment import (
    GeometryBranchEquipment,
)
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import (
    DistributionSubstation,
)
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.enums import Phase
from gdm.quantities import Voltage, Distance

from gdm.distribution.components.matrix_impedance_branch import MatrixImpedanceBranch


class GeometryBranch(DistributionBranchBase):
    """Data model for distribution branches based on line geometry."""

    equipment: Annotated[
        GeometryBranchEquipment,
        Field(..., description="Geometry branch equipment."),
    ]

    def validate_fields(self) -> "GeometryBranch":
        """Custom validator for geometry branch fields."""
        if len(self.phases) != len(self.equipment.conductors):
            msg = "Number of phases is not equal to number of wires."
            raise ValueError(msg)
        return self

    def to_matrix_representation(self) -> MatrixImpedanceBranch:
        """Convert geometry branch to matrix representation."""
        return MatrixImpedanceBranch(
            uuid=self.uuid,
            buses=self.buses,
            length=self.length,
            phases=self.phases,
            substation=self.substation,
            feeder=self.feeder,
            name=self.name,
            equipment=self.equipment.to_matrix_representation(self.phases.count(Phase.N)),
        )

    @classmethod
    def example(cls) -> "GeometryBranch":
        """Example for geometry branch."""
        bus1 = DistributionBus(
            voltage_type="line-to-ground",
            phases=[Phase.A, Phase.B, Phase.C],
            rated_voltage=Voltage(400, "volt"),
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            name="Branch-DistBus1",
        )
        bus2 = DistributionBus(
            voltage_type="line-to-ground",
            phases=[Phase.A, Phase.B, Phase.C],
            rated_voltage=Voltage(400, "volt"),
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            name="Branch-DistBus2",
        )
        return GeometryBranch(
            buses=[bus1, bus2],
            length=Distance(130.2, "meter"),
            phases=[Phase.A, Phase.B, Phase.C],
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            name="DistBranch1",
            equipment=GeometryBranchEquipment.example(),
        )
