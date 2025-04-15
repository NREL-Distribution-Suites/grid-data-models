"""This module contains distribution fuse."""

from typing import Annotated

from pydantic import Field

from gdm.distribution.components.base.distribution_switch_base import DistributionSwitchBase
from gdm.distribution.equipment.matrix_impedance_fuse_equipment import MatrixImpedanceFuseEquipment
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.enums import Phase
from gdm.quantities import PositiveVoltage, PositiveDistance
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.components.distribution_feeder import DistributionFeeder


class MatrixImpedanceFuse(DistributionSwitchBase):
    """Data model for distribution fuse."""

    equipment: Annotated[
        MatrixImpedanceFuseEquipment,
        Field(..., description="Matrix impedance branch equipment."),
    ]

    @classmethod
    def example(cls) -> "MatrixImpedanceFuse":
        bus1 = DistributionBus(
            voltage_type="line-to-ground",
            phases=[Phase.A, Phase.B, Phase.C],
            rated_voltage=PositiveVoltage(400, "volt"),
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            name="Branch-DistBus1",
        )
        bus2 = DistributionBus(
            voltage_type="line-to-ground",
            phases=[Phase.A, Phase.B, Phase.C],
            rated_voltage=PositiveVoltage(400, "volt"),
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            name="Branch-DistBus2",
        )
        return MatrixImpedanceFuse(
            buses=[bus1, bus2],
            length=PositiveDistance(130.2, "meter"),
            phases=[Phase.A, Phase.B, Phase.C],
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            name="DistBranch1",
            is_closed=[True, True, True],
            equipment=MatrixImpedanceFuseEquipment.example(),
        )
