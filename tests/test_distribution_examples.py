""" This module contains tests for all examples."""

import pytest

from gdm import (
    DistributionBus,
    DistributionComponent,
    PhaseVoltageSourceEquipment,
    VoltageSourceEquipment,
    DistributionVoltageSource,
    ConcentricCableEquipment,
    BareConductorEquipment,
    SequenceImpedanceBranchEquipment,
    MatrixImpedanceBranchEquipment,
    GeometryBranchEquipment,
    DistributionBranch,
    MatrixImpedanceBranch,
    SequenceImpedanceBranch,
    GeometryBranch,
    PhaseCapacitorEquipment,
    CapacitorEquipment,
    DistributionCapacitor,
    DistributionLoad,
    WindingEquipment,
    DistributionTransformer,
    DistributionTransformerEquipment,
    SolarEquipment,
    DistributionSolar,
)

DIST_INTERFACES = [
    DistributionBus,
    DistributionComponent,
    PhaseVoltageSourceEquipment,
    VoltageSourceEquipment,
    DistributionVoltageSource,
    ConcentricCableEquipment,
    BareConductorEquipment,
    SequenceImpedanceBranchEquipment,
    MatrixImpedanceBranchEquipment,
    GeometryBranchEquipment,
    DistributionBranch,
    MatrixImpedanceBranch,
    SequenceImpedanceBranch,
    GeometryBranch,
    PhaseCapacitorEquipment,
    CapacitorEquipment,
    DistributionCapacitor,
    DistributionLoad,
    WindingEquipment,
    DistributionTransformer,
    DistributionTransformerEquipment,
    SolarEquipment,
    DistributionSolar,
]


@pytest.mark.parametrize("dist_interface", DIST_INTERFACES)
def test_eval(dist_interface):
    assert dist_interface.example()
