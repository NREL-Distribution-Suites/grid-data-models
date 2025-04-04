# Distribution Regulator

## Single Phase Regulator

```python
>>> from gdm.distribution.components import (
...     DistributionSubstation, 
...     DistributionRegulator, 
...     DistributionFeeder, 
...     DistributionBus
... )
>>> from gdm.distribution.equipment import WindingEquipment, DistributionTransformerEquipment
>>> from gdm.distribution.controllers import RegulatorController
>>> from gdm.quantities import (
...     PositiveApparentPower, 
...     PositiveVoltage,
...     Time
... )
>>> from gdm.distribution.common import SequencePair
>>> from gdm.distribution.enums import (
...     ConnectionType,
...     VoltageTypes, 
...     Phase, 
... )
>>> bus_1 = DistributionBus(
...     name="Bus-1",
...     rated_voltage=PositiveVoltage(12.47, "kilovolts"),
...     phases=[Phase.A],
...     voltage_type=VoltageTypes.LINE_TO_GROUND,
... )

>>> bus_2 = DistributionBus(
...     name="Bus-2",
...     rated_voltage=PositiveVoltage(12.47, "kilovolts"),
...     phases=[Phase.A],
...     voltage_type=VoltageTypes.LINE_TO_GROUND,
... )

>>> regulator_equipment = DistributionTransformerEquipment(
...     name="SinglePhase-Regulator-1",
...     pct_full_load_loss=0.1,
...     pct_no_load_loss=0.002,
...     windings=[
...         WindingEquipment(
...             resistance=1.0,
...             is_grounded=False,
...             rated_voltage=PositiveVoltage(12.47, "kilovolts"),
...             rated_power=PositiveApparentPower(25, "kilova"),
...             num_phases=1,
...             tap_positions=[1.0],
...             connection_type=ConnectionType.STAR,
...             voltage_type=VoltageTypes.LINE_TO_GROUND,
...         ),
...         WindingEquipment(
...             resistance=1.0,
...             is_grounded=False,
...             rated_voltage=PositiveVoltage(12.47, "kilovolts"),
...             rated_power=PositiveApparentPower(25, "kilova"),
...             num_phases=1,
...             tap_positions=[1.0],
...             connection_type=ConnectionType.STAR,
...             voltage_type=VoltageTypes.LINE_TO_GROUND,
...         ),
...     ],
...     coupling_sequences=[SequencePair(from_index=0, to_index=1)],
...     winding_reactances=[2.3],
...     is_center_tapped=False,
... )

>>> regulator_controller = RegulatorController(
...     name="RegulatorController-1",
...     delay=Time(10, "seconds"),  # seconds
...     v_setpoint=PositiveVoltage(120, "volts"),  # volts
...     min_v_limit=PositiveVoltage(124, "volts"),
...     max_v_limit=PositiveVoltage(118, "volts"),
...     use_ldc=True,
...     is_reversible=False,
...     pt_ratio=60.0,
...     ldc_R=9,
...     ldc_X=3,
...     controlled_bus = bus_1,
...     controlled_phase = Phase.A,
...     ct_primary=700,
...     max_step=16,
...     bandwidth=3,  # volts
... )

>>> regulator_1 = DistributionRegulator(
...     name="Regulator-1",
...     buses=[bus_1, bus_2],
...     winding_phases=[[Phase.A], [Phase.A]],
...     equipment=regulator_equipment,
...     controllers=[regulator_controller],
... )
>>> regulator_1.pprint()
DistributionRegulator(
    name='Regulator-1',
    substation=None,
    feeder=None,
    in_service=True,
    buses=[
        DistributionBus(
            name='Bus-1',
            substation=None,
            feeder=None,
            voltage_type=<VoltageTypes.LINE_TO_GROUND: 'line-to-ground'>,
            phases=[<Phase.A: 'A'>],
            voltagelimits=[],
            rated_voltage=<Quantity(12.47, 'kilovolt')>,
            coordinate=None
        ),
        DistributionBus(
            name='Bus-2',
            substation=None,
            feeder=None,
            voltage_type=<VoltageTypes.LINE_TO_GROUND: 'line-to-ground'>,
            phases=[<Phase.A: 'A'>],
            voltagelimits=[],
            rated_voltage=<Quantity(12.47, 'kilovolt')>,
            coordinate=None
        )
    ],
    winding_phases=[[<Phase.A: 'A'>], [<Phase.A: 'A'>]],
    equipment=DistributionTransformerEquipment(
        name='SinglePhase-Regulator-1',
        pct_no_load_loss=0.002,
        pct_full_load_loss=0.1,
        windings=[
            WindingEquipment(
                name='',
                resistance=1.0,
                is_grounded=False,
                rated_voltage=<Quantity(12.47, 'kilovolt')>,
                voltage_type=<VoltageTypes.LINE_TO_GROUND: 'line-to-ground'>,
                rated_power=<Quantity(25, 'kilova')>,
                num_phases=1,
                connection_type=<ConnectionType.STAR: 'STAR'>,
                tap_positions=[1.0],
                total_taps=32,
                min_tap_pu=0.9,
                max_tap_pu=1.1
            ),
            WindingEquipment(
                name='',
                resistance=1.0,
                is_grounded=False,
                rated_voltage=<Quantity(12.47, 'kilovolt')>,
                voltage_type=<VoltageTypes.LINE_TO_GROUND: 'line-to-ground'>,
                rated_power=<Quantity(25, 'kilova')>,
                num_phases=1,
                connection_type=<ConnectionType.STAR: 'STAR'>,
                tap_positions=[1.0],
                total_taps=32,
                min_tap_pu=0.9,
                max_tap_pu=1.1
            )
        ],
        coupling_sequences=[SequencePair(from_index=0, to_index=1)],
        winding_reactances=[2.3],
        is_center_tapped=False
    ),
    controllers=[
        RegulatorController(
            name='RegulatorController-1',
            delay=<Quantity(10, 'second')>,
            v_setpoint=<Quantity(120, 'volt')>,
            min_v_limit=<Quantity(124, 'volt')>,
            max_v_limit=<Quantity(118, 'volt')>,
            pt_ratio=60.0,
            use_ldc=True,
            is_reversible=False,
            ldc_R=<Quantity(9, 'volt')>,
            ldc_X=<Quantity(3, 'volt')>,
            ct_primary=<Quantity(700, 'ampere')>,
            max_step=16,
            bandwidth=<Quantity(3, 'volt')>,
            controlled_bus=DistributionBus(
                name='Bus-1',
                substation=None,
                feeder=None,
                voltage_type=<VoltageTypes.LINE_TO_GROUND: 'line-to-ground'>,
                phases=[<Phase.A: 'A'>],
                voltagelimits=[],
                rated_voltage=<Quantity(12.47, 'kilovolt')>,
                coordinate=None
            ),
            controlled_phase=<Phase.A: 'A'>
        )
    ]
)

"""

```
