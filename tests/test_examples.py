""" This module contains tests for all examples."""
from rich import print

from gdm import (
    DistributionLoad,
    VoltageLimitSet,
    DistributionBus,
    ThermalLimitSet,
    DistributionVoltageSource,
    PhaseLoad,
    DistributionComponent,
    DistributionCapacitor,
    DistributionTransformer,
    WindingCoupling,
    PhaseWinding,
    DistributionAdmittanceMatrix,
    Winding,
    ImpedanceDistributionBranch,
    DistributionBranch,
    Conductor,
    DistributionModel,
    PhaseVoltageSource,
)
from gdm.capacitor import PowerSystemCapacitor
from gdm.load import PowerSystemLoad
from gdm.bus import PowerSystemBus


def test_bus():
    print(PowerSystemBus.example())


def test_capacitor():
    print(PowerSystemCapacitor.example())


def test_load():
    print(PowerSystemLoad.example())


def test_limitset():
    print(VoltageLimitSet.example())
    print(ThermalLimitSet.example())


def test_distribution_component():
    print(DistributionComponent.example())


def test_distribution_bus():
    print(DistributionBus.example())


def test_distribution_branch():
    print(Conductor.example())
    print(DistributionBranch.example())
    print(ImpedanceDistributionBranch.example())


def test_distribution_capacitor():
    print(DistributionCapacitor.example())


def test_distribution_load():
    print(PhaseLoad.example())
    print(DistributionLoad.example())


def test_distribution_voltage_source():
    print(DistributionVoltageSource.example())


def test_distribution_transformer():
    print(PhaseWinding.example())
    print(Winding.example())
    print(WindingCoupling.example())
    print(DistributionTransformer.example())


def test_distribution_model():
    print(DistributionModel.example())


def test_phase_voltage_source():
    print(PhaseVoltageSource.example())


def test_ybus_matrix():
    print(DistributionAdmittanceMatrix.example())
