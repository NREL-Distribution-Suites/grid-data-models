import pytest

from gdm import (
    DistributionRegulator,
    DistributionBus,
    Phase,
    PositiveVoltage,
    VoltageTypes,
    DistributionTransformerEquipment,
    WindingEquipment,
    PositiveApparentPower,
    ConnectionType,
    SequencePair,
)

# Three phase two winding regulators

BUS1 = DistributionBus(
    name="Bus1",
    phases=[Phase.A, Phase.B, Phase.C],
    nominal_voltage=PositiveVoltage(12.47, "kilovolts"),
    voltage_type=VoltageTypes.LINE_TO_LINE,
)


BUS2 = DistributionBus(
    name="Bus2",
    phases=[Phase.A, Phase.B, Phase.C],
    nominal_voltage=PositiveVoltage(0.4, "kilovolts"),
    voltage_type=VoltageTypes.LINE_TO_LINE,
)

WDG1 = WindingEquipment(
    name="wdg-1",
    resistance=0.3,
    is_grounded=True,
    nominal_voltage=PositiveVoltage(12.47, "kilovolts"),
    voltage_type=VoltageTypes.LINE_TO_LINE,
    rated_power=PositiveApparentPower(50, "kva"),
    num_phases=3,
    connection_type=ConnectionType.STAR,
    tap_positions=[1.0, 1.0, 1.0],
)
WDG2 = WindingEquipment(
    name="wdg-2",
    resistance=0.3,
    is_grounded=True,
    nominal_voltage=PositiveVoltage(0.4, "kilovolts"),
    voltage_type=VoltageTypes.LINE_TO_LINE,
    rated_power=PositiveApparentPower(50, "kva"),
    num_phases=3,
    connection_type=ConnectionType.STAR,
    tap_positions=[1.0, 1.0, 1.0],
)


def test_regulator_with_unequal_windings_and_contollers():
    with pytest.raises(ValueError):
        equipment = DistributionTransformerEquipment(
            name="Transformer-1",
            pct_full_load_loss=1.3,
            pct_no_load_loss=0.4,
            coupling_sequences=[SequencePair(0, 1)],
            winding_reactances=[0.4],
            is_center_tapped=False,
            windings=[WDG1, WDG2],
        )
        DistributionRegulator(
            name="test-regulator",
            buses=[BUS1, BUS2],
            winding_phases=[
                [Phase.A, Phase.B, Phase.C],
                [Phase.A, Phase.B, Phase.C],
            ],
            equipment=equipment,
            controllers=[],
        )
