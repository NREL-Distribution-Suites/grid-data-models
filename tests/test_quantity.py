from pydantic import ValidationError

from gdm.distribution.components import DistributionBus, DistributionSubstation, DistributionFeeder
from gdm.distribution.enums import Phase, VoltageTypes
from gdm.quantities import Voltage

import pytest


def test_bus_model():
    (
        DistributionBus(
            voltage_type=VoltageTypes.LINE_TO_LINE,
            name="Transformer-DistBus1",
            rated_voltage=Voltage(12.47, "kilovolt"),
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            phases=[Phase.A, Phase.B, Phase.C],
        ),
    )
    with pytest.raises(ValidationError):
        (
            DistributionBus(
                voltage_type=VoltageTypes.LINE_TO_LINE,
                name="Transformer-DistBus1",
                rated_voltage=Voltage(-12.47, "kilovolt"),
                substation=DistributionSubstation.example(),
                feeder=DistributionFeeder.example(),
                phases=[Phase.A, Phase.B, Phase.C],
            ),
        )
