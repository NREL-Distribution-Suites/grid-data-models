# Distribution Load

## Single Phase Constant Power Load

Creating a single-phase constant power load connected to a bus. A constant power load means that the power (both real and reactive) remains constant irrespective of voltage variations. The parameters p_real and p_imag are set to 1.0, indicating that the load is a constant power type.

```python
>>> from gdm.distribution.components import (
...     DistributionBus, 
...     DistributionLoad,
... )
>>> from gdm.distribution.equipment import (
...     PhaseLoadEquipment,
...     LoadEquipment,
... )
>>> from gdm.quantities import (
...     PositiveVoltage,
...     ReactivePower,
...     ActivePower,
... )
>>> from gdm.distribution.enums import Phase, VoltageTypes
>>> bus1 = DistributionBus(
...     name="Bus-1",
...     rated_voltage=PositiveVoltage(7.62, "kilovolts"),
...     voltage_type=VoltageTypes.LINE_TO_GROUND,
...     phases=[Phase.A]
... )
>>> phase_load_equipment = PhaseLoadEquipment(
...     name="Phase-Load-1",
...     real_power=ActivePower(3.5, "kilowatt"),
...     reactive_power=ReactivePower(0, "kilovar"),
...     z_real=0,
...     z_imag=0,
...     i_real=0,
...     i_imag=0,
...     p_real=1.0,
...     p_imag=1.0
... )
>>> load_equipment = LoadEquipment(
...     name="LoadEquipment-1",
...     phase_loads=[phase_load_equipment]
... )
>>> DistributionLoad(
...     name="Load-1",
...     bus=bus1,
...     phases=[Phase.A],
...     equipment=load_equipment
... ).pprint()
DistributionLoad(
    name='Load-1',
    substation=None,
    feeder=None,
    in_service=True,
    bus=DistributionBus(
        name='Bus-1',
        substation=None,
        feeder=None,
        voltage_type=<VoltageTypes.LINE_TO_GROUND: 'line-to-ground'>,
        phases=[<Phase.A: 'A'>],
        voltagelimits=[],
        rated_voltage=<Quantity(7.62, 'kilovolt')>,
        coordinate=None
    ),
    phases=[<Phase.A: 'A'>],
    equipment=LoadEquipment(
        name='LoadEquipment-1',
        phase_loads=[
            PhaseLoadEquipment(
                name='Phase-Load-1',
                real_power=<Quantity(3.5, 'kilowatt')>,
                reactive_power=<Quantity(0, 'kilovar')>,
                z_real=0.0,
                z_imag=0.0,
                i_real=0.0,
                i_imag=0.0,
                p_real=1.0,
                p_imag=1.0,
                num_customers=None
            )
        ],
        connection_type=<ConnectionType.STAR: 'STAR'>
    )
)

```

## Three Phase Delta Connected Constant Power Load


For the three-phase delta-connected constant power load, we need to define the load for all three phases (A, B, and C) and set the connection type to delta. In a delta connection, the load is connected between phases rather than from phase to neutral (as in a star connection).



```python
>>> from gdm.distribution.components import (
...     DistributionBus, 
...     DistributionLoad,
... )
>>> from gdm.distribution.equipment import (
...     PhaseLoadEquipment,
...     LoadEquipment,
... )
>>> from gdm.quantities import (
...     PositiveVoltage,
...     ReactivePower,
...     ActivePower,
... )
>>> from gdm.distribution.enums import Phase, VoltageTypes, ConnectionType
>>> bus2 = DistributionBus(
...     name="Bus-2",
...     rated_voltage=PositiveVoltage(13.8, "kilovolts"),
...     voltage_type=VoltageTypes.LINE_TO_LINE,
...     phases=[Phase.A, Phase.B, Phase.C]
... )
>>> phase_load_equipment_a = PhaseLoadEquipment(
...     name="Phase-Load-A",
...     real_power=ActivePower(5.0, "kilowatt"),
...     reactive_power=ReactivePower(2.0, "kilovar"),
...     z_real=0,
...     z_imag=0,
...     i_real=0,
...     i_imag=0,
...     p_real=1.0,
...     p_imag=1.0
... )
>>> phase_load_equipment_b = PhaseLoadEquipment(
...     name="Phase-Load-B",
...     real_power=ActivePower(5.0, "kilowatt"),
...     reactive_power=ReactivePower(2.0, "kilovar"),
...     z_real=0,
...     z_imag=0,
...     i_real=0,
...     i_imag=0,
...     p_real=1.0,
...     p_imag=1.0
... )
>>> phase_load_equipment_c = PhaseLoadEquipment(
...     name="Phase-Load-C",
...     real_power=ActivePower(5.0, "kilowatt"),
...     reactive_power=ReactivePower(2.0, "kilovar"),
...     z_real=0,
...     z_imag=0,
...     i_real=0,
...     i_imag=0,
...     p_real=1.0,
...     p_imag=1.0
... )
>>> load_equipment_delta = LoadEquipment(
...     name="LoadEquipment-Delta",
...     phase_loads=[phase_load_equipment_a, phase_load_equipment_b, phase_load_equipment_c],
...     connection_type=ConnectionType.DELTA
... )
>>> distribution_load_delta = DistributionLoad(
...     name="Load-Delta",
...     bus=bus2,
...     phases=[Phase.A, Phase.B, Phase.C],
...     equipment=load_equipment_delta
... )
>>> distribution_load_delta.pprint()
DistributionLoad(
    name='Load-Delta',
    substation=None,
    feeder=None,
    in_service=True,
    bus=DistributionBus(
        name='Bus-2',
        substation=None,
        feeder=None,
        voltage_type=<VoltageTypes.LINE_TO_LINE: 'line-to-line'>,
        phases=[<Phase.A: 'A'>, <Phase.B: 'B'>, <Phase.C: 'C'>],
        voltagelimits=[],
        rated_voltage=<Quantity(13.8, 'kilovolt')>,
        coordinate=None
    ),
    phases=[<Phase.A: 'A'>, <Phase.B: 'B'>, <Phase.C: 'C'>],
    equipment=LoadEquipment(
        name='LoadEquipment-Delta',
        phase_loads=[
            PhaseLoadEquipment(
                name='Phase-Load-A',
                real_power=<Quantity(5.0, 'kilowatt')>,
                reactive_power=<Quantity(2.0, 'kilovar')>,
                z_real=0.0,
                z_imag=0.0,
                i_real=0.0,
                i_imag=0.0,
                p_real=1.0,
                p_imag=1.0,
                num_customers=None
            ),
            PhaseLoadEquipment(
                name='Phase-Load-B',
                real_power=<Quantity(5.0, 'kilowatt')>,
                reactive_power=<Quantity(2.0, 'kilovar')>,
                z_real=0.0,
                z_imag=0.0,
                i_real=0.0,
                i_imag=0.0,
                p_real=1.0,
                p_imag=1.0,
                num_customers=None
            ),
            PhaseLoadEquipment(
                name='Phase-Load-C',
                real_power=<Quantity(5.0, 'kilowatt')>,
                reactive_power=<Quantity(2.0, 'kilovar')>,
                z_real=0.0,
                z_imag=0.0,
                i_real=0.0,
                i_imag=0.0,
                p_real=1.0,
                p_imag=1.0,
                num_customers=None
            )
        ],
        connection_type=<ConnectionType.DELTA: 'DELTA'>
    )
)

```