# Distribution Transformer

## Single Phase Transformer

A single-phase transformer with star (wye) connection. This example demonstrates creating a single-phase transformer with primary and secondary buses, winding equipment, and transformer configuration.

```python
>>> from gdm.distribution.components import (
...     DistributionTransformer,
...     DistributionSubstation,
...     DistributionFeeder,
...     DistributionBus, 
...     DistributionLoad,
... )
>>> from gdm.distribution.equipment import (
...     DistributionTransformerEquipment,
...     PhaseLoadEquipment,
...     WindingEquipment,
...     LoadEquipment,
... )
>>> from gdm.distribution.enums import (
...     ConnectionType,
...     VoltageTypes,
...     Phase,
... )
>>> from gdm.distribution.common import (
...     SequencePair,
... )
>>> from gdm.quantities import (
...     PositiveApparentPower,
...     PositiveVoltage,
...     ReactivePower,
...     ActivePower,
... )
>>> substation = DistributionSubstation(name='Test Substation', feeders=[DistributionFeeder(name='Test Feeder')])
>>> feeder = DistributionFeeder(name='Test Feeder')
>>> primary_bus = DistributionBus(
...     name='PrimaryBus',
...     substation=substation,
...     feeder=feeder,
...     voltage_type=VoltageTypes.LINE_TO_GROUND,
...     phases=[Phase.A],
...     rated_voltage=PositiveVoltage(7.62, "kilovolts")
... )
>>> secondary_bus = DistributionBus(
...     name='SecondaryBus',
...     substation=substation,
...     feeder=feeder,
...     voltage_type=VoltageTypes.LINE_TO_GROUND,
...     phases=[Phase.A],
...     rated_voltage=PositiveVoltage(0.24, "kilovolts")
... )
>>> primary_winding = WindingEquipment(
...     name='PrimaryWinding',
...     resistance=1.0,
...     is_grounded=True,
...     rated_voltage=PositiveVoltage(7.62, "kilovolts"),
...     voltage_type=VoltageTypes.LINE_TO_GROUND,
...     rated_power=PositiveApparentPower(56, "kilova"),
...     num_phases=1,
...     connection_type=ConnectionType.STAR,
...     tap_positions=[1.0],
...     total_taps=32,
...     min_tap_pu=0.9,
...     max_tap_pu=1.1
... )
>>> secondary_winding = WindingEquipment(
...     name='SecondaryWinding',
...     resistance=1.0,
...     is_grounded=True,
...     rated_voltage=PositiveVoltage(0.24, "kilovolts"),
...     voltage_type=VoltageTypes.LINE_TO_GROUND,
...     rated_power=PositiveApparentPower(56, "kilova"),
...     num_phases=1,
...     connection_type=ConnectionType.STAR,
...     tap_positions=[1.0],
...     total_taps=32,
...     min_tap_pu=0.9,
...     max_tap_pu=1.1
... )
>>> transformer_equipment = DistributionTransformerEquipment(
...     name='SinglePhaseTransformer',
...     pct_no_load_loss=0.1,
...     pct_full_load_loss=1.0,
...     windings=[primary_winding, secondary_winding],
...     coupling_sequences=[SequencePair(from_index=0, to_index=1)],
...     winding_reactances=[2.3],
...     is_center_tapped=False
... )
>>> single_phase_transformer = DistributionTransformer(
...     name='SinglePhaseTransformer1',
...     substation=substation,
...     feeder=feeder,
...     buses=[primary_bus, secondary_bus],
...     winding_phases=[[Phase.A], [Phase.A]],
...     equipment=transformer_equipment
... )
>>> single_phase_transformer.pprint()
DistributionTransformer(
    name='SinglePhaseTransformer1',
    substation=DistributionSubstation(
        name='Test Substation',
        feeders=[DistributionFeeder(name='Test Feeder')]
    ),
    feeder=DistributionFeeder(name='Test Feeder'),
    in_service=True,
    buses=[
        DistributionBus(
            name='PrimaryBus',
            substation=DistributionSubstation(
                name='Test Substation',
                feeders=[DistributionFeeder(name='Test Feeder')]
            ),
            feeder=DistributionFeeder(name='Test Feeder'),
            voltage_type=<VoltageTypes.LINE_TO_GROUND: 'line-to-ground'>,
            phases=[<Phase.A: 'A'>],
            voltagelimits=[],
            rated_voltage=<Quantity(7.62, 'kilovolt')>,
            coordinate=None
        ),
        DistributionBus(
            name='SecondaryBus',
            substation=DistributionSubstation(
                name='Test Substation',
                feeders=[DistributionFeeder(name='Test Feeder')]
            ),
            feeder=DistributionFeeder(name='Test Feeder'),
            voltage_type=<VoltageTypes.LINE_TO_GROUND: 'line-to-ground'>,
            phases=[<Phase.A: 'A'>],
            voltagelimits=[],
            rated_voltage=<Quantity(0.24, 'kilovolt')>,
            coordinate=None
        )
    ],
    winding_phases=[[<Phase.A: 'A'>], [<Phase.A: 'A'>]],
    equipment=DistributionTransformerEquipment(
        name='SinglePhaseTransformer',
        pct_no_load_loss=0.1,
        pct_full_load_loss=1.0,
        windings=[
            WindingEquipment(
                name='PrimaryWinding',
                resistance=1.0,
                is_grounded=True,
                rated_voltage=<Quantity(7.62, 'kilovolt')>,
                voltage_type=<VoltageTypes.LINE_TO_GROUND: 'line-to-ground'>,
                rated_power=<Quantity(56, 'kilova')>,
                num_phases=1,
                connection_type=<ConnectionType.STAR: 'STAR'>,
                tap_positions=[1.0],
                total_taps=32,
                min_tap_pu=0.9,
                max_tap_pu=1.1
            ),
            WindingEquipment(
                name='SecondaryWinding',
                resistance=1.0,
                is_grounded=True,
                rated_voltage=<Quantity(0.24, 'kilovolt')>,
                voltage_type=<VoltageTypes.LINE_TO_GROUND: 'line-to-ground'>,
                rated_power=<Quantity(56, 'kilova')>,
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
    )
)

```

## Three Phase Star Connected Transformer

A three-phase transformer with star (wye) connection. This example demonstrates creating a three-phase transformer with primary and secondary buses, winding equipment, and transformer configuration.

```python
>>> substation = DistributionSubstation(name='Test Substation', feeders=[DistributionFeeder(name='Test Feeder')])
>>> feeder = DistributionFeeder(name='Test Feeder')
>>> primary_bus_3p = DistributionBus(
...     name='PrimaryBus-3P',
...     substation=substation,
...     feeder=feeder,
...     voltage_type=VoltageTypes.LINE_TO_LINE,
...     phases=[Phase.A, Phase.B, Phase.C],
...     rated_voltage=PositiveVoltage(12.47, "kilovolts")
... )
>>> secondary_bus_3p = DistributionBus(
...     name='SecondaryBus-3P',
...     substation=substation,
...     feeder=feeder,
...     voltage_type=VoltageTypes.LINE_TO_LINE,
...     phases=[Phase.A, Phase.B, Phase.C],
...     rated_voltage=PositiveVoltage(0.4, "kilovolts")
... )
>>> primary_winding_3p = WindingEquipment(
...     name='PrimaryWinding-3P',
...     resistance=1.0,
...     is_grounded=False,
...     rated_voltage=PositiveVoltage(12.47, "kilovolts"),
...     voltage_type=VoltageTypes.LINE_TO_LINE,
...     rated_power=PositiveApparentPower(56, "kilova"),
...     num_phases=3,
...     connection_type=ConnectionType.STAR,
...     tap_positions=[1.0, 1.0, 1.0],
...     total_taps=32,
...     min_tap_pu=0.9,
...     max_tap_pu=1.1
... )
>>> secondary_winding_3p = WindingEquipment(
...     name='SecondaryWinding-3P',
...     resistance=1.0,
...     is_grounded=False,
...     rated_voltage=PositiveVoltage(0.4, "kilovolts"),
...     voltage_type=VoltageTypes.LINE_TO_LINE,
...     rated_power=PositiveApparentPower(56, "kilova"),
...     num_phases=3,
...     connection_type=ConnectionType.STAR,
...     tap_positions=[1.0, 1.0, 1.0],
...     total_taps=32,
...     min_tap_pu=0.9,
...     max_tap_pu=1.1
... )
>>> transformer_equipment_3p = DistributionTransformerEquipment(
...     name='ThreePhaseTransformer',
...     pct_no_load_loss=0.1,
...     pct_full_load_loss=1.0,
...     windings=[primary_winding_3p, secondary_winding_3p],
...     coupling_sequences=[SequencePair(from_index=0, to_index=1)],
...     winding_reactances=[2.3],
...     is_center_tapped=False
... )
>>> three_phase_transformer = DistributionTransformer(
...     name='ThreePhaseTransformer1',
...     substation=substation,
...     feeder=feeder,
...     buses=[primary_bus_3p, secondary_bus_3p],
...     winding_phases=[[Phase.A, Phase.B, Phase.C], [Phase.A, Phase.B,Phase.C]],
...     equipment=transformer_equipment_3p
... )
>>> three_phase_transformer.pprint()
DistributionTransformer(
    name='ThreePhaseTransformer1',
    substation=DistributionSubstation(
        name='Test Substation',
        feeders=[DistributionFeeder(name='Test Feeder')]
    ),
    feeder=DistributionFeeder(name='Test Feeder'),
    in_service=True,
    buses=[
        DistributionBus(
            name='PrimaryBus-3P',
            substation=DistributionSubstation(
                name='Test Substation',
                feeders=[DistributionFeeder(name='Test Feeder')]
            ),
            feeder=DistributionFeeder(name='Test Feeder'),
            voltage_type=<VoltageTypes.LINE_TO_LINE: 'line-to-line'>,
            phases=[<Phase.A: 'A'>, <Phase.B: 'B'>, <Phase.C: 'C'>],
            voltagelimits=[],
            rated_voltage=<Quantity(12.47, 'kilovolt')>,
            coordinate=None
        ),
        DistributionBus(
            name='SecondaryBus-3P',
            substation=DistributionSubstation(
                name='Test Substation',
                feeders=[DistributionFeeder(name='Test Feeder')]
            ),
            feeder=DistributionFeeder(name='Test Feeder'),
            voltage_type=<VoltageTypes.LINE_TO_LINE: 'line-to-line'>,
            phases=[<Phase.A: 'A'>, <Phase.B: 'B'>, <Phase.C: 'C'>],
            voltagelimits=[],
            rated_voltage=<Quantity(0.4, 'kilovolt')>,
            coordinate=None
        )
    ],
    winding_phases=[
        [<Phase.A: 'A'>, <Phase.B: 'B'>, <Phase.C: 'C'>],
        [<Phase.A: 'A'>, <Phase.B: 'B'>, <Phase.C: 'C'>]
    ],
    equipment=DistributionTransformerEquipment(
        name='ThreePhaseTransformer',
        pct_no_load_loss=0.1,
        pct_full_load_loss=1.0,
        windings=[
            WindingEquipment(
                name='PrimaryWinding-3P',
                resistance=1.0,
                is_grounded=False,
                rated_voltage=<Quantity(12.47, 'kilovolt')>,
                voltage_type=<VoltageTypes.LINE_TO_LINE: 'line-to-line'>,
                rated_power=<Quantity(56, 'kilova')>,
                num_phases=3,
                connection_type=<ConnectionType.STAR: 'STAR'>,
                tap_positions=[1.0, 1.0, 1.0],
                total_taps=32,
                min_tap_pu=0.9,
                max_tap_pu=1.1
            ),
            WindingEquipment(
                name='SecondaryWinding-3P',
                resistance=1.0,
                is_grounded=False,
                rated_voltage=<Quantity(0.4, 'kilovolt')>,
                voltage_type=<VoltageTypes.LINE_TO_LINE: 'line-to-line'>,
                rated_power=<Quantity(56, 'kilova')>,
                num_phases=3,
                connection_type=<ConnectionType.STAR: 'STAR'>,
                tap_positions=[1.0, 1.0, 1.0],
                total_taps=32,
                min_tap_pu=0.9,
                max_tap_pu=1.1
            )
        ],
        coupling_sequences=[SequencePair(from_index=0, to_index=1)],
        winding_reactances=[2.3],
        is_center_tapped=False
    )
)

```

## Split Phase Transformer

Primary delta connected split phase transformer.

```python
>>> bus_1 = DistributionBus(
...     name="Bus-1",
...     rated_voltage=PositiveVoltage(12.47, "kilovolts"),
...     phases=[Phase.A, Phase.B, Phase.C],
...     voltage_type=VoltageTypes.LINE_TO_LINE,
... )

>>> bus_2 = DistributionBus(
...     name="Bus-2",
...     rated_voltage=PositiveVoltage(0.24, "kilovolts"),
...     phases=[Phase.S1, Phase.N, Phase.S2],
...     voltage_type=VoltageTypes.LINE_TO_LINE,
... )

>>> bus_3 = DistributionBus(
...     name="Bus-3",
...     rated_voltage=PositiveVoltage(0.24, "kilovolts"),
...     phases=[Phase.S1, Phase.S2, Phase.N],
...     voltage_type=VoltageTypes.LINE_TO_LINE,
... )

>>> transformer_equipment = DistributionTransformerEquipment(
...     name="SplitPhase-Transformer-1",
...     pct_full_load_loss=0.2,
...     pct_no_load_loss=0.002,
...     windings=[
...         WindingEquipment(
...             resistance=0.02,
...             is_grounded=False,
...             rated_voltage=PositiveVoltage(12.47, "kilovolts"),
...             rated_power=PositiveApparentPower(25, "kilova"),
...             num_phases=1,
...             tap_positions=[1.0],
...             connection_type=ConnectionType.DELTA,
...             voltage_type=VoltageTypes.LINE_TO_LINE,
...         ),
...         WindingEquipment(
...             resistance=0.02,
...             is_grounded=False,
...             rated_voltage=PositiveVoltage(0.24, "kilovolts"),
...             rated_power=PositiveApparentPower(25, "kilova"),
...             num_phases=1,
...             tap_positions=[1.0],
...             connection_type=ConnectionType.DELTA,
...             voltage_type=VoltageTypes.LINE_TO_LINE,
...         ),
...         WindingEquipment(
...             resistance=0.02,
...             is_grounded=False,
...             rated_voltage=PositiveVoltage(0.24, "kilovolts"),
...             rated_power=PositiveApparentPower(25, "kilova"),
...             num_phases=1,
...             tap_positions=[1.0],
...             connection_type=ConnectionType.DELTA,
...             voltage_type=VoltageTypes.LINE_TO_LINE,
...         ),
...     ],
...     coupling_sequences=[
...         SequencePair(from_index=0, to_index=1),
...         SequencePair(from_index=1, to_index=2),
...         SequencePair(from_index=2, to_index=0),
...     ],
...     winding_reactances=[0.2, 0.2, 0.2],
...     is_center_tapped=True,
... )

>>> transformer_1 = DistributionTransformer(
...     name="Transformer-1",
...     buses=[bus_1, bus_2, bus_2],
...     winding_phases=[[Phase.A, Phase.B], [Phase.S1, Phase.N], [Phase.N, Phase.S2]],
...     equipment=transformer_equipment,
... )

>>> transformer_1.pprint()
DistributionTransformer(
    name='Transformer-1',
    substation=None,
    feeder=None,
    in_service=True,
    buses=[
        DistributionBus(
            name='Bus-1',
            substation=None,
            feeder=None,
            voltage_type=<VoltageTypes.LINE_TO_LINE: 'line-to-line'>,
            phases=[<Phase.A: 'A'>, <Phase.B: 'B'>, <Phase.C: 'C'>],
            voltagelimits=[],
            rated_voltage=<Quantity(12.47, 'kilovolt')>,
            coordinate=None
        ),
        DistributionBus(
            name='Bus-2',
            substation=None,
            feeder=None,
            voltage_type=<VoltageTypes.LINE_TO_LINE: 'line-to-line'>,
            phases=[<Phase.S1: 'S1'>, <Phase.N: 'N'>, <Phase.S2: 'S2'>],
            voltagelimits=[],
            rated_voltage=<Quantity(0.24, 'kilovolt')>,
            coordinate=None
        ),
        DistributionBus(
            name='Bus-3',
            substation=None,
            feeder=None,
            voltage_type=<VoltageTypes.LINE_TO_LINE: 'line-to-line'>,
            phases=[<Phase.S1: 'S1'>, <Phase.S2: 'S2'>, <Phase.N: 'N'>],
            voltagelimits=[],
            rated_voltage=<Quantity(0.24, 'kilovolt')>,
            coordinate=None
        )
    ],
    winding_phases=[
        [<Phase.A: 'A'>, <Phase.B: 'B'>],
        [<Phase.S1: 'S1'>, <Phase.N: 'N'>],
        [<Phase.N: 'N'>, <Phase.S2: 'S2'>]
    ],
    equipment=DistributionTransformerEquipment(
        name='SplitPhase-Transformer-1',
        pct_no_load_loss=0.002,
        pct_full_load_loss=0.2,
        windings=[
            WindingEquipment(
                name='',
                resistance=0.02,
                is_grounded=False,
                rated_voltage=<Quantity(12.47, 'kilovolt')>,
                voltage_type=<VoltageTypes.LINE_TO_LINE: 'line-to-line'>,
                rated_power=<Quantity(25, 'kilova')>,
                num_phases=1,
                connection_type=<ConnectionType.DELTA: 'DELTA'>,
                tap_positions=[1.0],
                total_taps=32,
                min_tap_pu=0.9,
                max_tap_pu=1.1
            ),
            WindingEquipment(
                name='',
                resistance=0.02,
                is_grounded=False,
                rated_voltage=<Quantity(0.24, 'kilovolt')>,
                voltage_type=<VoltageTypes.LINE_TO_LINE: 'line-to-line'>,
                rated_power=<Quantity(25, 'kilova')>,
                num_phases=1,
                connection_type=<ConnectionType.DELTA: 'DELTA'>,
                tap_positions=[1.0],
                total_taps=32,
                min_tap_pu=0.9,
                max_tap_pu=1.1
            ),
            WindingEquipment(
                name='',
                resistance=0.02,
                is_grounded=False,
                rated_voltage=<Quantity(0.24, 'kilovolt')>,
                voltage_type=<VoltageTypes.LINE_TO_LINE: 'line-to-line'>,
                rated_power=<Quantity(25, 'kilova')>,
                num_phases=1,
                connection_type=<ConnectionType.DELTA: 'DELTA'>,
                tap_positions=[1.0],
                total_taps=32,
                min_tap_pu=0.9,
                max_tap_pu=1.1
            )
        ],
        coupling_sequences=[
            SequencePair(from_index=0, to_index=1),
            SequencePair(from_index=1, to_index=2),
            SequencePair(from_index=2, to_index=0)
        ],
        winding_reactances=[0.2, 0.2, 0.2],
        is_center_tapped=True
    )
)

```


