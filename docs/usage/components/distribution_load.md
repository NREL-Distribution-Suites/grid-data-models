# Distribution Load

A single phase constant power load. `p_real` and `p_imag` set to 1 means that this distribution load is constant power load.
Feel free to play with other ZIP parameters to define different load characterstics.

```python
>>> from gdm import (
...     DistributionBus, 
...     DistributionLoad,
...     LoadEquipment,
...     PositiveVoltage,
...     VoltageTypes,
...     PhaseLoadEquipment,
...     Phase,
...     ActivePower,
...     ReactivePower
... )
>>> bus1 = DistributionBus(
...     name="Bus-1",
...     nominal_voltage=PositiveVoltage(7.62, "kilovolts"),
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
... )
DistributionLoad(name='Load-1', 
substation=None, 
feeder=None, 
bus=DistributionBus(name='Bus-1', 
    substation=None, 
    feeder=None, 
    voltage_type=<VoltageTypes.LINE_TO_GROUND: 'line-to-ground'>, 
    phases=[<Phase.A: 'A'>], 
    voltagelimits=[], 
    nominal_voltage=<Quantity(7.62, 'kilovolt')>, 
    coordinate=None), 
    phases=[<Phase.A: 'A'>], 
equipment=LoadEquipment(name='LoadEquipment-1', 
    phase_loads=[PhaseLoadEquipment(name='Phase-Load-1', 
        real_power=<Quantity(3.5, 'kilowatt')>, 
        reactive_power=<Quantity(0, 'kilovar')>, 
        z_real=0.0, 
        z_imag=0.0, 
        i_real=0.0, 
        i_imag=0.0, 
        p_real=1.0, 
        p_imag=1.0, 
        num_customers=None)], 
    connection_type=<ConnectionType.STAR: 'STAR'>))

```