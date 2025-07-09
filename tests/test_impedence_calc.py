from gdm.distribution.equipment import (
    GeometryBranchEquipment,
    BareConductorEquipment,
    ConcentricCableEquipment,
)
from gdm.distribution.components import GeometryBranch
from gdm.distribution.enums import WireInsulationType
from gdm.quantities import ResistancePULength, Distance, Current, Voltage

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
    # KERSTINGS EXAMPLE 1
    equip = GeometryBranchEquipment(
        name="test_kron_reduction_overhead_three_phase_with_neutral",
        conductors=[ACSR_336, ACSR_336, ACSR_336, ACSR_4_0],
        horizontal_positions=Distance([-4, -1.5, 3, 0], "feet"),
        vertical_positions=Distance([29, 29, 29, 25], "feet"),
    )
    branches = equip.to_matrix_representation(num_neutral=1)
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
    equip.to_matrix_representation(num_neutral=0)


def test_kron_reduction_overhead_two_phase_with_neutral():
    equip = GeometryBranchEquipment(
        name="test_kron_reduction_overhead_two_phase_with_neutral",
        conductors=[ACSR_336, ACSR_336, ACSR_4_0],
        horizontal_positions=Distance([-4, -1.5, 3], "feet"),
        vertical_positions=Distance([29, 29, 25], "feet"),
    )
    equip.to_matrix_representation(num_neutral=1)


def test_kron_reduction_overhead_two_phase():
    equip = GeometryBranchEquipment(
        name="test_kron_reduction_overhead_two_phase",
        conductors=[ACSR_336, ACSR_4_0],
        horizontal_positions=Distance([-4, -1.5], "feet"),
        vertical_positions=Distance([29, 29], "feet"),
    )
    equip.to_matrix_representation(num_neutral=0)


def test_kron_reduction_overhead_one_phase_with_neutral():
    equip = GeometryBranchEquipment(
        name="test_kron_reduction_overhead_one_phase_with_neutral",
        conductors=[ACSR_336, ACSR_4_0],
        horizontal_positions=Distance([-4, -1.5], "feet"),
        vertical_positions=Distance([29, 29], "feet"),
    )
    equip.to_matrix_representation(num_neutral=1)


def test_kron_reduction_overhead_one_phase():
    equip = GeometryBranchEquipment(
        name="test_kron_reduction_overhead_one_phase",
        conductors=[ACSR_336],
        horizontal_positions=Distance([-4], "feet"),
        vertical_positions=Distance([29], "feet"),
    )
    equip.to_matrix_representation(num_neutral=0)


def test_kron_reduction_underground_three_phase():
    # KERSTINGS EXAMPLE 2
    equip = GeometryBranchEquipment(
        name="test_kron_reduction_underground_three_phase",
        conductors=[CN_336, CN_336, CN_336],
        horizontal_positions=Distance([0, 6, 12], "inch"),
        vertical_positions=Distance([-3, -3, -3], "feet"),
    )
    equip.insulation = WireInsulationType.XLPE
    branches = equip.to_matrix_representation(num_neutral=0)
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
    equip.to_matrix_representation(num_neutral=0)


def test_kron_reduction_underground_one_phase():
    equip = GeometryBranchEquipment(
        name="test_kron_reduction_underground_one_phase",
        conductors=[CN_336],
        horizontal_positions=Distance([0], "inch"),
        vertical_positions=Distance([-3], "feet"),
    )
    equip.to_matrix_representation(num_neutral=0)


def test_geometry_barnch_with_conductors():
    g = GeometryBranch.example()
    g.to_maxtrix_representation()


def test_geometry_barnch_with_cables():
    g = GeometryBranch.example()
    g.equipment.conductors = [CN_336, CN_336, CN_336]
    g.to_maxtrix_representation()
