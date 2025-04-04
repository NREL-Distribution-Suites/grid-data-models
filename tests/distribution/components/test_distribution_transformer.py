import pytest

from gdm.distribution.components import (
    DistributionTransformer,
    DistributionBus,
)
from gdm.distribution.equipment import(
    DistributionTransformerEquipment,
    WindingEquipment,
)
from gdm.distribution.enums import (
    ConnectionType,
    VoltageTypes,
    Phase,
)
from gdm.distribution.common import(
    SequencePair,
)
from gdm.quantities import (
    PositiveApparentPower,
    PositiveVoltage,
)


def test_unequal_phase_length():
    with pytest.raises(ValueError):
        tr = DistributionTransformer.example()
        DistributionTransformer(
            name=tr.name,
            buses=tr.buses,
            winding_phases=[[Phase.A]],
            equipment=tr.equipment,
        )


@pytest.fixture(scope="module")
def buses():
    bus1 = DistributionBus(
        name="Bus1",
        rated_voltage=PositiveVoltage(12.47, "kilovolts"),
        voltage_type=VoltageTypes.LINE_TO_LINE,
        phases=[Phase.A, Phase.B, Phase.C],
    )
    bus2 = DistributionBus(
        name="Bus2",
        rated_voltage=PositiveVoltage(0.24, "kilovolts"),
        voltage_type=VoltageTypes.LINE_TO_LINE,
        phases=[Phase.S1, Phase.S2, Phase.N],
    )
    return [bus1, bus2]


@pytest.fixture(scope="module")
def ht_wdg():
    return WindingEquipment(
        resistance=0.02,
        is_grounded=False,
        rated_voltage=PositiveVoltage(12.47, "kilovolts"),
        rated_power=PositiveApparentPower(25, "kilova"),
        num_phases=1,
        tap_positions=[1.0],
        connection_type=ConnectionType.DELTA,
        voltage_type=VoltageTypes.LINE_TO_LINE,
    )


@pytest.fixture(scope="module")
def lt_wdg():
    return WindingEquipment(
        resistance=0.02,
        is_grounded=False,
        rated_voltage=PositiveVoltage(12.47, "kilovolts"),
        rated_power=PositiveApparentPower(25, "kilova"),
        num_phases=1,
        tap_positions=[1.0],
        connection_type=ConnectionType.DELTA,
        voltage_type=VoltageTypes.LINE_TO_LINE,
    )


@pytest.fixture(scope="module")
def split_phase_tr_equipment(ht_wdg, lt_wdg):
    return DistributionTransformerEquipment(
        name="SplitPhase-Transformer-1",
        pct_full_load_loss=0.2,
        pct_no_load_loss=0.002,
        coupling_sequences=[
            SequencePair(from_index=0, to_index=1),
            SequencePair(from_index=1, to_index=2),
            SequencePair(from_index=2, to_index=0),
        ],
        windings=[ht_wdg, lt_wdg, lt_wdg],
        winding_reactances=[0.2, 0.2, 0.2],
        is_center_tapped=True,
    )


def test_wrong_phase_length(buses, split_phase_tr_equipment):
    with pytest.raises(ValueError):
        DistributionTransformer(
            name="Tr-1",
            buses=buses,
            winding_phases=[
                [Phase.A, Phase.B, Phase.C],
                [Phase.S1, Phase.N],
                [Phase.N, Phase.S2],
            ],  # This is wrong
            equipment=split_phase_tr_equipment,
        )


def test_wrong_split_phase_length(buses, lt_wdg):
    with pytest.raises(ValueError):
        wrong_ht_wdg = WindingEquipment(
            resistance=0.02,
            is_grounded=False,
            rated_voltage=PositiveVoltage(12.47, "kilovolts"),
            rated_power=PositiveApparentPower(25, "kilova"),
            num_phases=2,  # This is wrong
            tap_positions=[1.0, 1.0],
            connection_type=ConnectionType.DELTA,
            voltage_type=VoltageTypes.LINE_TO_LINE,
        )
        DistributionTransformer(
            name="Tr-1",
            buses=buses,
            winding_phases=[[Phase.A, Phase.B], [Phase.S1, Phase.N], [Phase.N, Phase.S2]],
            equipment=DistributionTransformerEquipment(
                name="SplitPhase-Transformer-1",
                pct_full_load_loss=0.2,
                pct_no_load_loss=0.002,
                coupling_sequences=[
                    SequencePair(from_index=0, to_index=1),
                    SequencePair(from_index=1, to_index=2),
                    SequencePair(from_index=2, to_index=0),
                ],
                windings=[wrong_ht_wdg, lt_wdg, lt_wdg],
                winding_reactances=[0.2, 0.2, 0.2],
                is_center_tapped=True,
            ),
        )


def test_wrong_phase_connection(buses, split_phase_tr_equipment):
    with pytest.raises(ValueError):
        DistributionTransformer(
            name="Tr-1",
            buses=buses,
            winding_phases=[[Phase.A, Phase.B], [Phase.B], [Phase.B]],  # This is wrong
            equipment=split_phase_tr_equipment,
        )


def test_wrong_voltage_connection(split_phase_tr_equipment):
    with pytest.raises(ValueError):
        bus1 = DistributionBus(
            name="Bus1",
            rated_voltage=PositiveVoltage(8.8, "kilovolts"),  # This is wrong
            voltage_type=VoltageTypes.LINE_TO_LINE,
            phases=[Phase.A, Phase.B, Phase.C],
        )
        bus2 = DistributionBus(
            name="Bus2",
            rated_voltage=PositiveVoltage(0.24, "kilovolts"),
            voltage_type=VoltageTypes.LINE_TO_LINE,
            phases=[Phase.S1, Phase.S2, Phase.N],
        )

        DistributionTransformer(
            name="Tr-1",
            buses=[bus1, bus2],
            winding_phases=[[Phase.A, Phase.B], [Phase.S1, Phase.N], [Phase.N, Phase.S2]],
            equipment=split_phase_tr_equipment,
        )
