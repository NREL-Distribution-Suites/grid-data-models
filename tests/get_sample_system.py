"""Module for creating test system."""

from infrasys.quantities import ActivePower

from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.components.distribution_transformer import DistributionTransformer
from gdm.distribution.equipment.distribution_transformer_equipment import (
    DistributionTransformerEquipment,
    WindingEquipment,
)
from gdm.distribution.components.matrix_impedance_branch import MatrixImpedanceBranch
from gdm.distribution.components.distribution_load import DistributionLoad
from gdm.distribution.distribution_enum import ConnectionType, Phase, VoltageTypes
from gdm import DistributionSystem
from gdm.distribution.equipment.load_equipment import LoadEquipment
from gdm.distribution.equipment.matrix_impedance_branch_equipment import (
    MatrixImpedanceBranchEquipment,
)
from gdm.distribution.equipment.phase_load_equipment import PhaseLoadEquipment
from gdm.distribution.sequence_pair import SequencePair
from gdm.quantities import (
    CapacitancePULength,
    PositiveApparentPower,
    PositiveCurrent,
    PositiveDistance,
    PositiveResistancePULength,
    PositiveVoltage,
    ReactancePULength,
)
from gdm.quantities import ReactivePower


def get_three_bus_system():
    """Create a three bus system."""

    sys = DistributionSystem(auto_add_composed_components=True)
    bus_1 = DistributionBus(
        name="Bus-1",
        nominal_voltage=PositiveVoltage(12.47, "kilovolts"),
        phases=[Phase.A, Phase.B, Phase.C],
        voltage_type=VoltageTypes.LINE_TO_LINE,
    )
    bus_2 = DistributionBus(
        name="Bus-2",
        nominal_voltage=PositiveVoltage(0.24, "kilovolts"),
        phases=[Phase.S1, Phase.N, Phase.S2],
        voltage_type=VoltageTypes.LINE_TO_LINE,
    )
    bus_3 = DistributionBus(
        name="Bus-3",
        nominal_voltage=PositiveVoltage(0.24, "kilovolts"),
        phases=[Phase.S1, Phase.S2, Phase.N],
        voltage_type=VoltageTypes.LINE_TO_LINE,
    )
    sys.add_components(bus_1, bus_2, bus_3)
    transformer_1 = DistributionTransformer(
        name="Transformer-1",
        buses=[bus_1, bus_2],
        winding_phases=[[Phase.A, Phase.B], [Phase.S1, Phase.N], [Phase.N, Phase.S2]],
        equipment=DistributionTransformerEquipment(
            name="SplitPhase-Transformer-1",
            pct_full_load_loss=0.2,
            pct_no_load_loss=0.002,
            windings=[
                WindingEquipment(
                    resistance=0.02,
                    is_grounded=False,
                    nominal_voltage=PositiveVoltage(12.47, "kilovolts"),
                    rated_power=PositiveApparentPower(25, "kilova"),
                    num_phases=1,
                    tap_positions=[1.0],
                    connection_type=ConnectionType.DELTA,
                    voltage_type=VoltageTypes.LINE_TO_LINE,
                ),
                WindingEquipment(
                    resistance=0.02,
                    is_grounded=False,
                    nominal_voltage=PositiveVoltage(0.24, "kilovolts"),
                    rated_power=PositiveApparentPower(25, "kilova"),
                    num_phases=1,
                    tap_positions=[1.0],
                    connection_type=ConnectionType.DELTA,
                    voltage_type=VoltageTypes.LINE_TO_LINE,
                ),
                WindingEquipment(
                    resistance=0.02,
                    is_grounded=False,
                    nominal_voltage=PositiveVoltage(0.24, "kilovolts"),
                    rated_power=PositiveApparentPower(25, "kilova"),
                    num_phases=1,
                    tap_positions=[1.0],
                    connection_type=ConnectionType.DELTA,
                    voltage_type=VoltageTypes.LINE_TO_LINE,
                ),
            ],
            coupling_sequences=[
                SequencePair(from_index=0, to_index=1),
                SequencePair(from_index=1, to_index=2),
                SequencePair(from_index=2, to_index=0),
            ],
            winding_reactances=[0.2, 0.2, 0.2],
            is_center_tapped=True,
        ),
    )
    sys.add_component(transformer_1)

    line_1 = MatrixImpedanceBranch(
        name="AC Line Segment 1",
        buses=[bus_2, bus_3],
        phases=[Phase.S1, Phase.S2, Phase.N],
        length=PositiveDistance(20, "m"),
        equipment=MatrixImpedanceBranchEquipment(
            name="matrix-impedance-branch-1",
            r_matrix=PositiveResistancePULength(
                [
                    [0.08820, 0.0312137],
                    [0.0312137, 0.0901946],
                ],
                "ohm/mi",
            ),
            x_matrix=ReactancePULength(
                [
                    [0.20744, 0.0935314],
                    [0.0935314, 0.200783],
                ],
                "ohm/mi",
            ),
            c_matrix=CapacitancePULength(
                [
                    [2.90301, -0.679335],
                    [-0.679335, 3.15896],
                ],
                "nanofarad/mi",
            ),
            ampacity=PositiveCurrent(90, "ampere"),
        ),
    )
    sys.add_component(line_1)
    load_1 = DistributionLoad(
        name="Load-1",
        bus=bus_3,
        phases=[Phase.S1, Phase.S2],
        equipment=LoadEquipment(
            name="Load-Equipment-1",
            connection_type=ConnectionType.DELTA,
            phase_loads=[
                PhaseLoadEquipment(
                    name="phase-1-load-equipment",
                    num_customers=1,
                    real_power=ActivePower(2.5, "kilowatt"),
                    reactive_power=ReactivePower(0, "kilovar"),
                    z_real=0.75,
                    z_imag=1.0,
                    i_real=0.1,
                    i_imag=0.0,
                    p_real=0.15,
                    p_imag=0.0,
                ),
                PhaseLoadEquipment(
                    name="phase-1-load-equipment",
                    num_customers=1,
                    real_power=ActivePower(2.5, "kilowatt"),
                    reactive_power=ReactivePower(0.3, "kilovar"),
                    z_real=0.0,
                    z_imag=0.0,
                    i_real=0.0,
                    i_imag=0.0,
                    p_real=1.0,
                    p_imag=1.0,
                ),
            ],
        ),
    )
    sys.add_component(load_1)
    return sys
