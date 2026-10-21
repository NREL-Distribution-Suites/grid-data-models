import importlib
import json

import numpy as np
import pytest
from infrasys import serialization

from gdm.systems.distribution import DistributionSystem
from gdm.systems.distribution.components import (
    DistributionLoad,
    DistributionTransformer,
    MatrixImpedanceSwitch,
    SequenceImpedanceSwitch,
)
from gdm.systems.distribution.equipment import (
    DistributionTransformerEquipment,
    PhaseLoadEquipment,
    SequenceImpedanceBranchEquipment,
    SequenceImpedanceBranchEquipmentBase,
    SequenceImpedanceSwitchEquipment,
)
from gdm.systems.distribution.enums import Phase


def block_ditto_imports(monkeypatch):
    import_module = importlib.import_module

    def reject_ditto_import(name, package=None):
        if name == "ditto" or name.startswith("ditto."):
            raise AssertionError(f"Unexpected Ditto import while loading GDM: {name}")
        return import_module(name, package)

    monkeypatch.setattr(serialization.importlib, "import_module", reject_ditto_import)


def test_generic_equipment_roundtrip_without_ditto(tmp_path, monkeypatch):
    system = DistributionSystem(auto_add_composed_components=True)
    load = DistributionLoad.example()
    phase = load.equipment.phase_loads[0]
    phase.min_voltage_pu = 0.85
    phase.max_voltage_pu = 1.05
    phase.cutoff_voltage_pu = 0.5
    transformer_equipment = DistributionTransformerEquipment.example()
    transformer_equipment.magnetizing_current_pct = 1.0
    switch = SequenceImpedanceSwitch.example()
    system.add_components(load, transformer_equipment, switch)
    filename = tmp_path / "system.json"
    system.to_json(filename)
    raw_data = json.loads(filename.read_text())
    assert raw_data["supplemental_attributes"] == []
    assert "ditto" not in filename.read_text()
    block_ditto_imports(monkeypatch)
    restored = DistributionSystem.from_json(filename)
    restored_phase = restored.get_component_by_uuid(phase.uuid)
    assert restored_phase.min_voltage_pu == 0.85
    assert restored_phase.max_voltage_pu == 1.05
    assert restored_phase.cutoff_voltage_pu == 0.5
    assert restored.get_component_by_uuid(transformer_equipment.uuid).magnetizing_current_pct == 1
    assert isinstance(restored.get_component_by_uuid(switch.uuid), SequenceImpedanceSwitch)
    for model in (DistributionLoad, MatrixImpedanceSwitch, PhaseLoadEquipment):
        assert not any(field.startswith("opendss_") for field in model.model_fields)


def test_sequence_equipment_reuses_base_and_converts_units():
    assert issubclass(SequenceImpedanceBranchEquipment, SequenceImpedanceBranchEquipmentBase)
    assert issubclass(SequenceImpedanceSwitchEquipment, SequenceImpedanceBranchEquipmentBase)
    equipment = SequenceImpedanceSwitchEquipment.example()
    equipment.zero_seq_resistance = equipment.zero_seq_resistance.to("ohm/km")
    matrix = equipment.to_matrix_equipment()
    np.testing.assert_allclose(
        np.diag(matrix.r_matrix.to("ohm/mi").magnitude), (0.45 + 2 * 0.304) / 3
    )
    assert matrix.r_matrix.to("ohm/mi").magnitude[0, 1] == pytest.approx((0.45 - 0.304) / 3)
    np.testing.assert_allclose(np.diag(matrix.c_matrix.magnitude), (700 + 2 * 900) / 3)
    assert matrix.c_matrix.magnitude[0, 1] == pytest.approx((700 - 900) / 3)


def test_load_aggregation_and_split_preserve_voltage_behavior():
    phase = PhaseLoadEquipment.example()
    phase.min_voltage_pu = 0.9
    phase.cutoff_voltage_pu = 0.4
    aggregate = PhaseLoadEquipment.aggregate([phase, phase], "combined")
    assert aggregate.min_voltage_pu == 0.9
    assert aggregate.cutoff_voltage_pu == 0.4
    split = PhaseLoadEquipment.split(phase, 2)
    assert split.min_voltage_pu == phase.min_voltage_pu
    assert split.cutoff_voltage_pu == phase.cutoff_voltage_pu
    assert split.real_power == phase.real_power / 2
    other = phase.model_copy(update={"min_voltage_pu": 0.85})
    with pytest.raises(ValueError, match="different min_voltage_pu"):
        PhaseLoadEquipment.aggregate([phase, other], "invalid")


@pytest.mark.parametrize(
    "updates",
    [
        {"phases": ["A", "B"], "is_closed": [True, True]},
        {"is_closed": [True]},
        {"phases": ["A", "B", "C", "A"], "is_closed": [True] * 4},
        {"buses": []},
    ],
)
def test_sequence_switch_rejects_invalid_connectivity(updates):
    switch = SequenceImpedanceSwitch.example()
    with pytest.raises(ValueError):
        SequenceImpedanceSwitch(**(dict(switch) | updates))


def test_parallel_switch_conductors_roundtrip_without_ditto(tmp_path, monkeypatch):
    template = MatrixImpedanceSwitch.example()
    switch = MatrixImpedanceSwitch(
        **(
            dict(template)
            | {
                "phases": [Phase.B, Phase.C],
                "conductor_phases": [Phase.B, Phase.B, Phase.C],
                "is_closed": [True, False, True],
            }
        )
    )
    assert switch.num_conductors == 3
    system = DistributionSystem(auto_add_composed_components=True)
    system.add_component(switch)
    path = tmp_path / "parallel-switch.json"
    system.to_json(path)
    block_ditto_imports(monkeypatch)
    restored = DistributionSystem.from_json(path).get_component(MatrixImpedanceSwitch, switch.name)
    assert restored.phases == [Phase.B, Phase.C]
    assert restored.conductor_phases == [Phase.B, Phase.B, Phase.C]
    assert restored.is_closed == [True, False, True]
    assert restored.num_conductors == 3


@pytest.mark.parametrize(
    "updates",
    [
        {"conductor_phases": []},
        {"conductor_phases": [Phase.B, Phase.B]},
        {"conductor_phases": [Phase.B, Phase.C]},
        {"conductor_phases": [Phase.A, Phase.B, Phase.C]},
        {"is_closed": [True, True]},
        {"phases": [Phase.B, Phase.B, Phase.C]},
    ],
)
def test_parallel_switch_conductor_validation(updates):
    fields = dict(MatrixImpedanceSwitch.example()) | {
        "phases": [Phase.B, Phase.C],
        "conductor_phases": [Phase.B, Phase.B, Phase.C],
        "is_closed": [True, True, True],
    }
    with pytest.raises(ValueError):
        MatrixImpedanceSwitch(**(fields | updates))


def test_matrix_switch_rejects_different_bus_voltages():
    switch = MatrixImpedanceSwitch.example()
    with pytest.raises(ValueError, match="rating should be same"):
        switch.buses = DistributionTransformer.example().buses
