"""This module contains geometry branch."""

from typing import Annotated

from pydantic import Field

from gdm.distribution.components.distribution_branch import DistributionBranch
from gdm.distribution.equipment.geometry_branch_equipment import GeometryBranchEquipment


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
            name=base_branch.name,
            equipment=GeometryBranchEquipment.example(),
        )
