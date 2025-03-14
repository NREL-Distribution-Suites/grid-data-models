from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from infrasys import SingleTimeSeries, NonSequentialTimeSeries

from gdm.distribution.equipment.inverter_equipment import InverterEquipment
from gdm.distribution.equipment.solar_equipment import SolarEquipment
from gdm.distribution.controllers.distribution_inverter_controller import (
    PowerfactorInverterController,
)
from gdm import (
    DistributionTransformerEquipment,
    MatrixImpedanceBranchEquipment,
    DistributionVoltageSource,
    DistributionTransformer,
    PhaseCapacitorEquipment,
    DistributionCapacitor,
    MatrixImpedanceBranch,
    PositiveReactivePower,
    PositiveApparentPower,
    DistributionInverter,
    PositiveActivePower,
    CapacitancePULength,
    DistributionSystem,
    CapacitorEquipment,
    PhaseLoadEquipment,
    ResistancePULength,
    DistributionSolar,
    ActivePowerPUTime,
    ReactancePULength,
    WindingEquipment,
    PositiveDistance,
    DistributionLoad,
    PositiveCurrent,
    PositiveVoltage,
    DistributionBus,
    ConnectionType,
    LoadEquipment,
    ReactivePower,
    VoltageTypes,
    SequencePair,
    ActivePower,
    Irradiance,
    Phase,
)


def build_distribution_buses():
    return [
        DistributionBus.example().model_copy(update={"uuid": uuid4(), "name": f"bus_{i}"})
        for i in range(10)
    ]


def build_distribution_load(bus: DistributionBus, bus_number: int):
    return DistributionLoad.example().model_copy(
        update={
            "uuid": uuid4(),
            "name": f"load_{bus_number}",
            "bus": bus,
            "equipment": LoadEquipment.example().model_copy(
                update={
                    "uuid": uuid4(),
                    "name": f"load_equipment_{bus_number}",
                    "phase_loads": [
                        PhaseLoadEquipment.example().model_copy(
                            update={
                                "uuid": uuid4(),
                                "name": f"phase_load_{i}_{bus_number}",
                                "real_power": ActivePower(bus_number + 1, "kilowatt"),
                                "reactive_power": ReactivePower(
                                    (bus_number + 1) * 0.44, "kilovar"
                                ),
                            }
                        )
                        for i in range(3)
                    ],
                }
            ),
        }
    )


def build_distribution_solar(bus: DistributionBus, bus_number: int):
    return DistributionSolar.example().model_copy(
        update={
            "uuid": uuid4(),
            "name": f"solar_{bus_number}",
            "bus": bus,
            "inverter": DistributionInverter.example().model_copy(
                update={
                    "uuid": uuid4(),
                    "name": f"inverter_{bus_number}",
                    "controller": PowerfactorInverterController.example(),
                    "equipment": InverterEquipment.example().model_copy(
                        update={
                            "uuid": uuid4(),
                            "name": f"inverter_equipment_{bus_number}",
                            "capacity": PositiveApparentPower(bus_number + 1, "kilowatt"),
                        }
                    ),
                }
            ),
            "equipment": SolarEquipment.example().model_copy(
                update={
                    "uuid": uuid4(),
                    "name": f"solar_equipment_{bus_number}",
                    "solar_capacity": ActivePower(bus_number + 1, "kilowatt"),
                    "rated_capacity": PositiveActivePower(bus_number + 1, "kilowatt"),
                    "resistance": 1,
                    "reactance": 1,
                }
            ),
        }
    )


def build_distribution_line(bus1: DistributionBus, bus2: DistributionBus):
    return MatrixImpedanceBranch.example().model_copy(
        update={
            "name": f"line_{bus1.name}_{bus2.name}",
            "uuid": uuid4(),
            "buses": [bus1, bus2],
        }
    )


def build_distribution_capacitor(bus: DistributionBus, bus_number: int):
    return DistributionCapacitor.example().model_copy(
        update={
            "name": f"capacitor_{bus.name}",
            "uuid": uuid4(),
            "bus": bus,
            "equipment": CapacitorEquipment.example().model_copy(
                update={
                    "uuid": uuid4(),
                    "name": f"capacitor_equipment_{bus_number}",
                    "phase_capacitors": [
                        PhaseCapacitorEquipment.example().model_copy(
                            update={
                                "uuid": uuid4(),
                                "name": f"phase_capacitor_{i}_{bus_number}",
                                "rated_capacity": PositiveReactivePower(bus_number + 1, "kvar"),
                            }
                        )
                        for i in range(3)
                    ],
                }
            ),
        }
    )


def build_distribution_xfmr(bus1: DistributionBus, bus2: DistributionBus):
    return DistributionTransformer.example().model_copy(
        update={
            "name": "substation_xfmr",
            "uuid": uuid4(),
            "buses": [bus1, bus2],
        }
    )


def build_distribution_voltage_source(bus: DistributionBus):
    return DistributionVoltageSource.example().model_copy(
        update={
            "bus": bus,
        }
    )


def build_source_bus():
    return DistributionBus.example().model_copy(
        update={
            "name": "src_bus",
            "uuid": uuid4(),
            "nominal_voltage": PositiveVoltage(12.47, "kilovolt"),
        }
    )


def build_split_phase_distribution_buses():
    return [
        DistributionBus.example().model_copy(
            update={
                "uuid": uuid4(),
                "name": f"split_phase_bus_{i}",
                "phases": [Phase.S1, Phase.S2, Phase.N],
                "nominal_voltage": PositiveVoltage(120, "volt"),
                "voltage_type": VoltageTypes.LINE_TO_GROUND,
            }
        )
        for i in range(10)
    ]


def build_split_phase_distribution_xfmr(bus1: DistributionBus, bus2: DistributionBus):
    return DistributionTransformer(
        name="split_phase_xfmr",
        buses=[bus1, bus2],
        winding_phases=[[Phase.A, Phase.B], [Phase.S1, Phase.N], [Phase.S2, Phase.N]],
        equipment=DistributionTransformerEquipment(
            name="split_phase_xfmr_equipment",
            pct_no_load_loss=0.1,
            pct_full_load_loss=1,
            is_center_tapped=True,
            coupling_sequences=[SequencePair(0, 1), SequencePair(0, 2), SequencePair(1, 2)],
            winding_reactances=[2.3] * 3,
            windings=[
                WindingEquipment(
                    resistance=1,
                    is_grounded=False,
                    nominal_voltage=PositiveVoltage(0.4, "kilovolt"),
                    rated_power=PositiveApparentPower(50, "kilova"),
                    connection_type=ConnectionType.STAR,
                    num_phases=1,
                    tap_positions=[1.0],
                    voltage_type=VoltageTypes.LINE_TO_LINE,
                ),
                WindingEquipment(
                    resistance=1,
                    is_grounded=True,
                    nominal_voltage=PositiveVoltage(120, "volt"),
                    rated_power=PositiveApparentPower(50, "kilova"),
                    connection_type=ConnectionType.STAR,
                    num_phases=1,
                    tap_positions=[1.0],
                    voltage_type=VoltageTypes.LINE_TO_GROUND,
                ),
                WindingEquipment(
                    resistance=1,
                    is_grounded=True,
                    nominal_voltage=PositiveVoltage(120, "volt"),
                    rated_power=PositiveApparentPower(50, "kilova"),
                    connection_type=ConnectionType.STAR,
                    num_phases=1,
                    tap_positions=[1.0],
                    voltage_type=VoltageTypes.LINE_TO_GROUND,
                ),
            ],
        ),
    )


def build_split_phase_matrix_impedance():
    return MatrixImpedanceBranchEquipment(
        name="matrix-impedance-branch-1",
        r_matrix=ResistancePULength(
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
    )


def build_split_phase_distribution_line(
    bus1: DistributionBus, bus2: DistributionBus, matrix: MatrixImpedanceBranchEquipment
):
    return MatrixImpedanceBranch(
        buses=[bus1, bus2],
        length=PositiveDistance(130.2, "meter"),
        phases=[Phase.S1, Phase.S2, Phase.N],
        name="DistBranch_{}_{}".format(bus1.name, bus2.name),
        equipment=matrix,
    )


def build_split_phase_loads(bus: DistributionBus, bus_number: int):
    return [
        DistributionLoad(
            name=f"load_{bus_number}_{phase}",
            bus=bus,
            phases=[phase],
            equipment=LoadEquipment(
                name=f"load_equipment_{bus_number}_{phase}",
                connection_type=ConnectionType.STAR,
                phase_loads=[
                    PhaseLoadEquipment(
                        name=f"phase_load_{bus_number}_{phase}",
                        real_power=ActivePower(bus_number + 1, "kilowatt"),
                        reactive_power=ReactivePower((bus_number + 1) * 0.44, "kilovar"),
                        z_real=0.75,
                        z_imag=1.0,
                        i_real=0.1,
                        i_imag=0.0,
                        p_real=0.15,
                        p_imag=0.0,
                    )
                ],
            ),
        )
        for phase in bus.phases
        if phase != Phase.N
    ]


def build_split_phase_solar(bus: DistributionBus, bus_number: int):
    return DistributionSolar(
        name=f"pv_{bus_number}",
        bus=bus,
        phases=[Phase.S1, Phase.S2],
        equipment=SolarEquipment(
            name=f"pv_equipment_{bus_number}",
            rated_capacity=ActivePower(bus_number + 1, "kilowatt"),
            solar_power=ActivePower(bus_number + 1, "kilowatt"),
            resistance=1,
            reactance=1,
        ),
        inverter=DistributionInverter(
            name=f"pv_inverter_{bus_number}",
            controller=PowerfactorInverterController.example(),
            equipment=InverterEquipment(
                capacity=PositiveApparentPower(3.8, "kva"),
                rise_limit=ActivePowerPUTime(1.1, "kW/second"),
                fall_limit=ActivePowerPUTime(1.1, "kW/second"),
                cutin_percent=10,
                cutout_percent=10,
            ),
        ),
    )


@pytest.fixture(name="simple_distribution_system")
def sample_distribution_system() -> DistributionSystem:
    """Tests the DistributionSystem class."""

    # building primary
    system = DistributionSystem(auto_add_composed_components=True)
    buses = build_distribution_buses()
    load_bus_numbers = [5, 7, 9]
    solar_bus_numbers = [3, 9]
    capacity_bus_numbers = [4, 8]

    for bus_number, bus in enumerate(buses):
        system.add_component(bus)
        if bus_number in load_bus_numbers:
            load = build_distribution_load(bus, bus_number)
            system.add_component(load)
        if bus_number in solar_bus_numbers:
            solar = build_distribution_solar(bus, bus_number)
            system.add_component(solar)
        if bus_number in capacity_bus_numbers:
            capacitor = build_distribution_capacitor(bus, bus_number)
            system.add_component(capacitor)
        if bus_number != 0:
            line = build_distribution_line(buses[bus_number - 1], bus)
            system.add_component(line)

    # building substation
    src_bus = build_source_bus()
    substation_xfmr = build_distribution_xfmr(src_bus, buses[0])
    system.add_component(substation_xfmr)
    vsource = build_distribution_voltage_source(src_bus)
    system.add_component(vsource)

    # building secondary
    split_phase_buses = build_split_phase_distribution_buses()
    system.add_components(*split_phase_buses)
    split_phase_xfmr = build_split_phase_distribution_xfmr(buses[-1], split_phase_buses[0])
    system.add_component(split_phase_xfmr)

    split_phase_load_bus_numbers = [5, 7, 9]
    split_phase_solar_bus_numbers = [3, 9]
    matrix = build_split_phase_matrix_impedance()
    for bus_number, bus in enumerate(split_phase_buses):
        if bus_number != 0:
            split_phase_line = build_split_phase_distribution_line(
                split_phase_buses[bus_number - 1], bus, matrix
            )
            system.add_component(split_phase_line)
        if bus_number in split_phase_load_bus_numbers:
            split_phase_loads = build_split_phase_loads(bus, bus_number)
            system.add_components(*split_phase_loads)
        if bus_number in split_phase_solar_bus_numbers:
            distribution_solar = build_split_phase_solar(bus, bus_number)
            system.add_component(distribution_solar)

    return system


@pytest.fixture(name="distribution_system_with_single_timeseries")
def sample_distribution_system_with_single_timeseries(
    simple_distribution_system,
) -> DistributionSystem:
    system = simple_distribution_system
    load_profile_kw = SingleTimeSeries.from_array(
        data=ActivePower([1, 2, 3, 4, 5], "kilowatt"),
        variable_name="active_power",
        initial_time=datetime(2020, 1, 1),
        resolution=timedelta(minutes=30),
    )
    load_profile_kvar = SingleTimeSeries.from_array(
        data=ActivePower([1, 2, 3, 4, 5], "kilovar"),
        variable_name="reactive_power",
        initial_time=datetime(2020, 1, 1),
        resolution=timedelta(minutes=30),
    )
    loads: list[DistributionLoad] = list(system.get_components(DistributionLoad))
    system.add_time_series(
        load_profile_kw,
        *loads,
        profile_type="PMult",
        profile_name="load_profile_kw",
        use_actual=True,
    )
    system.add_time_series(
        load_profile_kvar,
        *loads,
        profile_type="QMult",
        profile_name="load_profile_kvar",
        use_actual=False,
    )

    irradiance_profile = SingleTimeSeries.from_array(
        data=Irradiance([0, 0.5, 1, 0.5, 0], "kilowatt / meter ** 2"),
        variable_name="irradiance",
        initial_time=datetime(2020, 1, 1),
        resolution=timedelta(minutes=30),
    )
    pvs: list[DistributionSolar] = list(system.get_components(DistributionSolar))
    system.add_time_series(
        irradiance_profile, *pvs, profile_type="PMult", profile_name="pv_profile", use_actual=False
    )
    return system


@pytest.fixture(name="distribution_system_with_nonsequential_timeseries")
def sample_distribution_system_with_nonsequential_timeseries(
    simple_distribution_system,
) -> DistributionSystem:
    system = simple_distribution_system
    load_profile_kw = NonSequentialTimeSeries.from_array(
        data=ActivePower([1, 2, 3, 4, 5], "kilowatt"),
        timestamps=[
            datetime(2020, 1, 1),
            datetime(2020, 1, 3),
            datetime(2020, 2, 1),
            datetime(2020, 2, 3),
            datetime(2020, 3, 1),
        ],
        variable_name="active_power",
    )
    load_profile_kvar = NonSequentialTimeSeries.from_array(
        data=ActivePower([1, 2, 3, 4, 5], "kilovar"),
        timestamps=[
            datetime(2020, 1, 1),
            datetime(2020, 1, 3),
            datetime(2020, 2, 1),
            datetime(2020, 2, 3),
            datetime(2020, 3, 1),
        ],
        variable_name="reactive_power",
    )
    loads: list[DistributionLoad] = list(system.get_components(DistributionLoad))
    system.add_time_series(
        load_profile_kw,
        *loads,
        profile_type="PMult",
        profile_name="load_profile_kw",
        use_actual=True,
    )
    system.add_time_series(
        load_profile_kvar,
        *loads,
        profile_type="QMult",
        profile_name="load_profile_kvar",
        use_actual=False,
    )

    irradiance_profile = NonSequentialTimeSeries.from_array(
        data=Irradiance([0, 0.5, 1, 0.5, 0], "kilowatt / meter ** 2"),
        timestamps=[
            datetime(2020, 1, 1),
            datetime(2020, 1, 3),
            datetime(2020, 2, 1),
            datetime(2020, 2, 3),
            datetime(2020, 3, 1),
        ],
        variable_name="irradiance",
    )
    pvs: list[DistributionSolar] = list(system.get_components(DistributionSolar))
    system.add_time_series(
        irradiance_profile, *pvs, profile_type="PMult", profile_name="pv_profile", use_actual=False
    )
    return system
