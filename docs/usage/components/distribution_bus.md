# Distribution Bus

Single phase bus.

```python
>>> from gdm import (
...     DistributionBus, 
...     PositiveVoltage,
...     VoltageTypes,
...     Phase
... )
>>> DistributionBus(
...     name="Bus-1",
...     nominal_voltage=PositiveVoltage(7.62, "kilovolts"),
...     voltage_type=VoltageTypes.LINE_TO_GROUND,
...     phases=[Phase.A]
... )
DistributionBus(name='Bus-1', substation=None, feeder=None, voltage_type=<VoltageTypes.LINE_TO_GROUND: 'line-to-ground'>, phases=[<Phase.A: 'A'>], voltagelimits=[], nominal_voltage=<Quantity(7.62, 'kilovolt')>, coordinate=None)

```

Three phase bus.

```python
>>> DistributionBus(
...     name="Bus-1",
...     nominal_voltage=PositiveVoltage(7.62, "kilovolts"),
...     voltage_type=VoltageTypes.LINE_TO_GROUND,
...     phases=[Phase.A, Phase.B, Phase.C]
... )
DistributionBus(name='Bus-1', substation=None, feeder=None, voltage_type=<VoltageTypes.LINE_TO_GROUND: 'line-to-ground'>, phases=[<Phase.A: 'A'>, <Phase.B: 'B'>, <Phase.C: 'C'>], voltagelimits=[], nominal_voltage=<Quantity(7.62, 'kilovolt')>, coordinate=None)

```

A bus with cartesian coordinates.

```python
>>> from gdm import Location
>>> DistributionBus(
...     name="Bus-1",
...     nominal_voltage=PositiveVoltage(7.62, "kilovolts"),
...     voltage_type=VoltageTypes.LINE_TO_GROUND,
...     phases=[Phase.A, Phase.B, Phase.C],
...     coordinate=Location(x=10.0, y=20.0)
... )
DistributionBus(name='Bus-1', substation=None, feeder=None, voltage_type=<VoltageTypes.LINE_TO_GROUND: 'line-to-ground'>, phases=[<Phase.A: 'A'>, <Phase.B: 'B'>, <Phase.C: 'C'>], voltagelimits=[], nominal_voltage=<Quantity(7.62, 'kilovolt')>, coordinate=Location(name='', x=10.0, y=20.0, crs=None))

```

A bus with coordinate reference system.

```python
>>> from gdm import Location
>>> DistributionBus(
...     name="Bus-1",
...     nominal_voltage=PositiveVoltage(7.62, "kilovolts"),
...     voltage_type=VoltageTypes.LINE_TO_GROUND,
...     phases=[Phase.A, Phase.B, Phase.C],
...     coordinate=Location(x=10.0, y=20.0, crs='epsg:4326')
... )
DistributionBus(name='Bus-1', substation=None, feeder=None, voltage_type=<VoltageTypes.LINE_TO_GROUND: 'line-to-ground'>, phases=[<Phase.A: 'A'>, <Phase.B: 'B'>, <Phase.C: 'C'>], voltagelimits=[], nominal_voltage=<Quantity(7.62, 'kilovolt')>, coordinate=Location(name='', x=10.0, y=20.0, crs='epsg:4326'))

```