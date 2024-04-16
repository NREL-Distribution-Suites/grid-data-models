from infrasys import Location

from gdm import (
    Phase,
    VoltageTypes,
    DistributionBus,
    DistributionComponent,
    DistributionFeeder,
    DistributionSubstation,
    VoltageLimitSet,
    LimitType,
)
from gdm.quantities import PositiveVoltage


def test_single_phase_bus():
    bus = DistributionBus(
        name="Bus-1",
        phases=[Phase.A],
        voltage_type=VoltageTypes.LINE_TO_GROUND,
        nominal_voltage=PositiveVoltage(400, "volt"),
    )
    assert bus.name == "Bus-1"
    assert bus.phases == [Phase.A]
    assert bus.voltage_type == VoltageTypes.LINE_TO_GROUND
    assert bus.nominal_voltage == PositiveVoltage(400, "volt")


def test_three_phase_bus():
    bus = DistributionBus(
        name="Three-Phase-Bus",
        phases=[Phase.A, Phase.B, Phase.C],
        voltage_type=VoltageTypes.LINE_TO_LINE,
        nominal_voltage=PositiveVoltage(13.2, "kilovolt"),
    )
    assert bus.name == "Three-Phase-Bus"
    assert bus.phases == [Phase.A, Phase.B, Phase.C]
    assert bus.voltage_type == VoltageTypes.LINE_TO_LINE
    assert bus.nominal_voltage == PositiveVoltage(13200, "volt")


def test_bus_with_cartesian_coordinates():
    bus1 = DistributionBus(
        name="Bus-1",
        phases=[Phase.A],
        voltage_type=VoltageTypes.LINE_TO_GROUND,
        nominal_voltage=PositiveVoltage(400, "volt"),
        coordinate=Location(x=10, y=20),
    )
    assert bus1.coordinate.x == 10
    assert bus1.coordinate.y == 20


def test_bus_with_epsg_coordinate():
    bus = DistributionBus(
        name="Bus-1",
        phases=[Phase.A],
        voltage_type=VoltageTypes.LINE_TO_GROUND,
        nominal_voltage=PositiveVoltage(400, "volt"),
        coordinate=Location(x=10, y=20, crs="epsg:4326"),
    )
    assert bus.coordinate.crs == "epsg:4326"


def test_bus_with_feeder_and_substation():
    feeder = DistributionFeeder(name="Feeder-1")
    substation = DistributionSubstation(
        name="Substation-1", feeders=[DistributionFeeder(name="Feeder-1")]
    )
    bus = DistributionBus(
        name="Bus-1",
        phases=[Phase.A],
        voltage_type=VoltageTypes.LINE_TO_GROUND,
        nominal_voltage=PositiveVoltage(400, "volt"),
        belongs_to=DistributionComponent(feeder=feeder, substation=substation),
    )
    assert bus.belongs_to.feeder == feeder
    assert bus.belongs_to.substation == substation


def test_bus_with_voltage_limits():
    min_voltage_limit = VoltageLimitSet(
        limit_type=LimitType.MIN, value=PositiveVoltage(400 * 0.9, "volt")
    )
    max_voltage_limit = VoltageLimitSet(
        limit_type=LimitType.MAX, value=PositiveVoltage(400 * 1.1, "volt")
    )
    bus = DistributionBus(
        name="Bus-1",
        phases=[Phase.A],
        voltage_type=VoltageTypes.LINE_TO_GROUND,
        nominal_voltage=PositiveVoltage(400, "volt"),
        voltagelimits=[min_voltage_limit, max_voltage_limit],
    )
    assert bus.voltagelimits[0] == min_voltage_limit
    assert bus.voltagelimits[1] == max_voltage_limit
