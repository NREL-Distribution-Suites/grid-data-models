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
from gdm.distribution.equipment.bare_conductor_equipment import BareConductorEquipment
from gdm.distribution.equipment.concentric_cable_equipment import ConcentricCableEquipment

from gdm.distribution.distribution_enum import Phase
from gdm.quantities import PositiveVoltage, PositiveDistance


class GeometryBranch(DistributionBranchBase):
    """Interface for geometry based lines."""

    conductors: Annotated[
        list[BareConductorEquipment | ConcentricCableEquipment],
        Field(..., description="List of overhead wires or cables."),
    ]

    geometry: Annotated[
        GeometryBranchEquipment,
        Field(..., description="Geometry branch equipment."),
    ]

    def validate_fields(self) -> "GeometryBranch":
        """Custom validator for geometry branch fields."""
        if len(self.phases) != len(self.conductors):
            msg = "Number of phases is not equal to number of wires."
            raise ValueError(msg)

        if not self.conductors:
            msg = f"Number of wires must be at least 1 {self.conductors=}"
            raise ValueError(msg)

        if len(self.geometry.horizontal_positions) != len(self.conductors):
            msg = f"{self.equipment.horizontal_positions} and {self.conductors=} must be equal in length."
            raise ValueError(msg)

        if len(self.geometry.vertical_positions) != len(self.conductors):
            msg = f"{self.equipment.vertical_positions} and {self.conductors=} must be equal in length."
            raise ValueError(msg)


        return self

    @classmethod
    def example(cls) -> "GeometryBranch":
        """Example for geometry branch."""
        bus1 = DistributionBus(
            voltage_type="line-to-ground",
            phases=[Phase.A, Phase.B, Phase.C],
            nominal_voltage=PositiveVoltage(400, "volt"),
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            conductors=[BareConductorEquipment.example()] * 3,
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
        return GeometryBranch(
            buses=[bus1, bus2],
            length=PositiveDistance(130.2, "meter"),
            phases=[Phase.A, Phase.B, Phase.C],
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            name="DistBranch1",
            equipment=GeometryBranchEquipment.example(),
        )
