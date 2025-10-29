from gdm.distribution.equipment import (
    GeometryBranchEquipment,
    BareConductorEquipment,
    ConcentricCableEquipment,
)
from gdm.distribution.components import (
    GeometryBranch,
    DistributionVoltageSource,
    DistributionBus,
    MatrixImpedanceBranch,
)
from gdm.quantities import ResistancePULength, Distance, Current, Voltage
from gdm.distribution.enums import WireInsulationType, Phase
from gdm.distribution import DistributionSystem

import numpy as np

ACSR_4_0 = BareConductorEquipment(
    name="4/0_6/1_ACSR",
    ac_resistance=ResistancePULength(0.5920, "ohm/mile"),
    dc_resistance=ResistancePULength(0.5920 * 0.9, "ohm/mile"),
    conductor_diameter=Distance(0.563, "inches"),
    conductor_gmr=Distance(0.00814, "feet"),
    ampacity=Current(200, "ampere"),
    emergency_ampacity=Current(200 * 1.2, "ampere"),
)

ACSR_336 = BareConductorEquipment(
    name="336_400_26/7_ACSR",
    ac_resistance=ResistancePULength(0.306, "ohm/mile"),
    dc_resistance=ResistancePULength(0.306 * 0.9, "ohm/mile"),
    conductor_diameter=Distance(0.721, "inches"),
    conductor_gmr=Distance(0.0244, "feet"),
    ampacity=Current(300, "ampere"),
    emergency_ampacity=Current(300 * 1.2, "ampere"),
)

CN_336 = ConcentricCableEquipment(
    name="336,400 26/7",
    conductor_gmr=Distance(0.0171, "feet"),
    strand_gmr=Distance(0.00208, "feet"),
    phase_ac_resistance=ResistancePULength(0.4100, "ohm/mile"),
    strand_ac_resistance=ResistancePULength(14.8722, "ohm/mile"),
    cable_diameter=Distance(1.29, "inch"),
    insulation_diameter=Distance(1.16, "inch"),
    strand_diameter=Distance(0.0641, "inch"),
    conductor_diameter=Distance(0.567, "inch"),
    ampacity=Current(260, "ampere"),
    num_neutral_strands=13,
    insulation_thickness=Distance(0.008, "in"),
    rated_voltage=Voltage(25, "kilovolt"),
)


def test_kron_reduction_overhead_three_phase_with_neutral():
    # William H Kerstings, Distribution System Modeling and Analysis,
    # Z calculation - Chapter 4, example 4.1
    # C calculation - Chapter 5, example 5.1
    equip = GeometryBranchEquipment(
        name="test_kron_reduction_overhead_three_phase_with_neutral",
        conductors=[ACSR_336, ACSR_336, ACSR_336, ACSR_4_0],
        horizontal_positions=Distance([-4, -1.5, 3, 0], "feet"),
        vertical_positions=Distance([29, 29, 29, 25], "feet"),
    )
    branches = equip.to_matrix_representation()
    assert branches.r_matrix.shape == (4, 4)

    branches.kron_reduce(phases=[Phase.A, Phase.B, Phase.C, Phase.N])

    r_from_kerstings = np.array(
        [[0.4575, 0.1560, 0.1535], [0.1560, 0.4666, 0.1580], [0.1535, 0.1580, 0.4615]]
    )
    x_from_kerstings = np.array(
        [[1.0780, 0.5017, 0.3849], [0.5017, 1.0482, 0.4236], [0.3849, 0.4236, 1.0651]]
    )
    c_from_kerstings = np.array(
        [[0.0150, -0.0049, -0.0019], [-0.0049, 0.0159, -0.0031], [-0.0019, -0.0031, 0.0143]]
    )

    assert np.allclose(branches.r_matrix.magnitude, r_from_kerstings, atol=1e-3, rtol=1e-3)
    assert np.allclose(branches.x_matrix.magnitude, x_from_kerstings, atol=1e-3, rtol=1e-3)
    assert np.allclose(branches.c_matrix.magnitude, c_from_kerstings, atol=1e-3, rtol=1e-3)


def test_kron_reduction_overhead_three_phase():
    equip = GeometryBranchEquipment(
        name="test_kron_reduction_overhead_three_phase",
        conductors=[ACSR_336, ACSR_336, ACSR_336],
        horizontal_positions=Distance([-4, -1.5, 3], "feet"),
        vertical_positions=Distance([29, 29, 29], "feet"),
    )
    branch = equip.to_matrix_representation()
    assert branch.r_matrix.shape == (3, 3)


def test_kron_reduction_overhead_two_phase_with_neutral():
    equip = GeometryBranchEquipment(
        name="test_kron_reduction_overhead_two_phase_with_neutral",
        conductors=[ACSR_336, ACSR_336, ACSR_4_0],
        horizontal_positions=Distance([-4, -1.5, 3], "feet"),
        vertical_positions=Distance([29, 29, 25], "feet"),
    )
    branch = equip.to_matrix_representation()
    assert branch.r_matrix.shape == (3, 3)


def test_kron_reduction_overhead_two_phase():
    equip = GeometryBranchEquipment(
        name="test_kron_reduction_overhead_two_phase",
        conductors=[ACSR_336, ACSR_4_0],
        horizontal_positions=Distance([-4, -1.5], "feet"),
        vertical_positions=Distance([29, 29], "feet"),
    )
    branch = equip.to_matrix_representation()
    assert branch.r_matrix.shape == (2, 2)


def test_kron_reduction_overhead_one_phase_with_neutral():
    equip = GeometryBranchEquipment(
        name="test_kron_reduction_overhead_one_phase_with_neutral",
        conductors=[ACSR_336, ACSR_4_0],
        horizontal_positions=Distance([-4, -1.5], "feet"),
        vertical_positions=Distance([29, 29], "feet"),
    )
    branch = equip.to_matrix_representation()
    assert branch.r_matrix.shape == (2, 2)


def test_kron_reduction_overhead_one_phase():
    equip = GeometryBranchEquipment(
        name="test_kron_reduction_overhead_one_phase",
        conductors=[ACSR_336],
        horizontal_positions=Distance([-4], "feet"),
        vertical_positions=Distance([29], "feet"),
    )
    branch = equip.to_matrix_representation()
    assert branch.r_matrix.shape == (1, 1)


def test_kron_reduction_underground_three_phase():
    # William H Kerstings, Distribution System Modeling and Analysis,
    # Z calculation - Chapter 4, example 4.2
    # C calculation - Chapter 5, example 5.2
    equip = GeometryBranchEquipment(
        name="test_kron_reduction_underground_three_phase",
        conductors=[CN_336, CN_336, CN_336],
        horizontal_positions=Distance([0, 6, 12], "inch"),
        vertical_positions=Distance([-3, -3, -3], "feet"),
    )
    equip.insulation = WireInsulationType.XLPE
    branches = equip.to_matrix_representation()
    branches.kron_reduce(phases=[Phase.A, Phase.B, Phase.C, Phase.N, Phase.N, Phase.N])
    r_from_kerstings = np.array(
        [[0.7981, 0.3191, 0.2849], [0.3191, 0.7891, 0.3191], [0.2849, 0.3191, 0.7981]]
    )
    x_from_kerstings = np.array(
        [[0.4463, 0.0328, -0.0143], [0.0328, 0.4041, 0.0328], [-0.0143, 0.0328, 0.4463]]
    )
    c_from_kerstings = np.array([[96.5569, 0, 0], [0, 96.5569, 0], [0, 0, 96.5569]])

    print(np.isclose(branches.c_matrix.magnitude, c_from_kerstings, atol=1e-3, rtol=1e-3))

    assert np.allclose(branches.r_matrix.magnitude, r_from_kerstings, atol=1e-3, rtol=1e-3)
    assert np.allclose(branches.x_matrix.magnitude, x_from_kerstings, atol=1e-3, rtol=1e-3)
    assert np.allclose(
        np.diag(branches.c_matrix.magnitude), np.diag(c_from_kerstings), atol=1e-3, rtol=1e-3
    )


def test_kron_reduction_underground_two_phase():
    equip = GeometryBranchEquipment(
        name="test_kron_reduction_underground_two_phase",
        conductors=[CN_336, CN_336],
        horizontal_positions=Distance([0, 6], "inch"),
        vertical_positions=Distance([-3, -3], "feet"),
    )
    branch = equip.to_matrix_representation()
    assert branch.r_matrix.shape == (4, 4)


def test_kron_reduction_underground_one_phase():
    equip = GeometryBranchEquipment(
        name="test_kron_reduction_underground_one_phase",
        conductors=[CN_336],
        horizontal_positions=Distance([0], "inch"),
        vertical_positions=Distance([-3], "feet"),
    )
    branch = equip.to_matrix_representation()
    assert branch.r_matrix.shape == (2, 2)


def test_geometry_barnch_with_conductors():
    g = GeometryBranch.example()
    branch = g.to_matrix_representation()
    assert branch.equipment.r_matrix.shape == (3, 3)


def test_geometry_barnch_with_cables():
    g = GeometryBranch.example()
    g.equipment.conductors = [CN_336, CN_336, CN_336]
    branch = g.to_matrix_representation()
    assert branch.equipment.r_matrix.shape == (3, 3)


def my_system():
    system = DistributionSystem(auto_add_composed_components=True)
    for i in range(10):
        geometry_branch = GeometryBranch.example()
        geometry_branch = geometry_branch.model_copy(
            update={
                "name": f"branch_{i}",
                "phases": [Phase.A, Phase.B, Phase.C, Phase.N],
                "equipment": geometry_branch.equipment.model_copy(
                    update={
                        "conductors": [ACSR_336, ACSR_336, ACSR_336, ACSR_4_0],
                        "horizontal_positions": Distance([0, 3, 6, 0], "feet"),
                        "vertical_positions": Distance([30, 30, 30, 25], "feet"),
                    }
                ),
            }
        )
        geometry_branch.buses[0] = geometry_branch.buses[0].model_copy(
            update={
                "name": f"bus_{i}",
                "phases": [Phase.A, Phase.B, Phase.C, Phase.N],
            }
        )
        geometry_branch.buses[1] = geometry_branch.buses[1].model_copy(
            update={
                "name": f"bus_{i + 1}",
                "phases": [Phase.A, Phase.B, Phase.C, Phase.N],
            }
        )

        if i > 0:
            geometry_branch.buses[0] = bus_1  # noqa
        else:
            v_source = DistributionVoltageSource.example()
            v_source.bus = geometry_branch.buses[0]
            system.add_component(v_source)
        system.add_component(geometry_branch)
        bus_1 = geometry_branch.buses[1]

    for i in range(10):
        geometry_branch = GeometryBranch.example()
        geometry_branch = geometry_branch.model_copy(
            update={
                "name": f"cable_{i}",
                "equipment": geometry_branch.equipment.model_copy(
                    update={
                        "conductors": [CN_336, CN_336, CN_336],
                    }
                ),
            }
        )
        geometry_branch.buses[0] = bus_1
        geometry_branch.buses[1] = geometry_branch.buses[1].model_copy(
            update={"name": f"bus_{i + 20}"}
        )

        system.add_component(geometry_branch)
        bus_1 = geometry_branch.buses[1]

    return system


def test_kron_reduce_system():
    system = my_system()
    system.kron_reduce()

    for bus in system.get_components(DistributionBus):
        assert Phase.N not in bus.phases

    for branch in system.get_components(MatrixImpedanceBranch):
        assert Phase.N not in branch.phases
