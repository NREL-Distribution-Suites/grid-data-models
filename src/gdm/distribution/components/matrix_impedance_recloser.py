"""This module contains matrix impedance recloser device."""

from typing import Annotated

from pydantic import Field

from gdm.distribution.components.base.distribution_switch_base import DistributionSwitchBase
from gdm.distribution.equipment.matrix_impedance_recloser_equipment import (
    MatrixImpedanceRecloserEquipment,
)
from gdm.distribution.controllers.distribution_recloser_controller import (
    DistributionRecloserController,
)
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.distribution_enum import Phase
from gdm.quantities import PositiveVoltage, PositiveDistance
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.components.distribution_feeder import DistributionFeeder


class MatrixImpedanceRecloser(DistributionSwitchBase):
    """Interface for distribution recloser."""

    equipment: Annotated[
        MatrixImpedanceRecloserEquipment,
        Field(..., description="Matrix impedance recloser equipment."),
    ]
    controller: Annotated[
        DistributionRecloserController, Field(..., description="Instance of recloser controller.")
    ]

    @classmethod
    def example(cls) -> "MatrixImpedanceRecloser":
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
        return MatrixImpedanceRecloser(
            buses=[bus1, bus2],
            length=PositiveDistance(130.2, "meter"),
            phases=[Phase.A, Phase.B, Phase.C],
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            name="DistBranch1",
            is_closed=[True, True, True],
            equipment=MatrixImpedanceRecloserEquipment.example(),
            controller=DistributionRecloserController.example(),
        )
