""" This module contains interface for distribution transformer."""

from gdm.distribution.distribution_enum import Phase, VoltageTypes
from gdm.quantities import PositiveVoltage
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.equipment.distribution_transformer_equipment import (
    DistributionTransformerEquipment,
)
from gdm.distribution.components.base.distribution_transformer_base import (
    DistributionTransformerBase,
)


class DistributionTransformer(DistributionTransformerBase):
    """Interface for defining distribution transformer."""

    @classmethod
    def example(cls) -> "DistributionTransformer":
        """Example for distribution transformer."""
        return DistributionTransformer(
            name="DistributionTransformer1",
            buses=[
                DistributionBus(
                    voltage_type=VoltageTypes.LINE_TO_LINE,
                    name="Transformer-DistBus1",
                    nominal_voltage=PositiveVoltage(12.47, "kilovolt"),
                    substation=DistributionSubstation.example(),
                    feeder=DistributionFeeder.example(),
                    phases=[Phase.A, Phase.B, Phase.C],
                ),
                DistributionBus(
                    voltage_type=VoltageTypes.LINE_TO_LINE,
                    name="Transformer-DistBus2",
                    nominal_voltage=PositiveVoltage(0.4, "kilovolt"),
                    substation=DistributionSubstation.example(),
                    feeder=DistributionFeeder.example(),
                    phases=[Phase.A, Phase.B, Phase.C],
                ),
            ],
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            winding_phases=[[Phase.A, Phase.B, Phase.C], [Phase.A, Phase.B, Phase.C]],
            equipment=DistributionTransformerEquipment.example(),
        )
