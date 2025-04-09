import pytest

from gdm.distribution.components import (
    DistributionBattery,
    DistributionSolar,
    DistributionBus,
)
from gdm.distribution.equipment import (
    InverterEquipment,
    BatteryEquipment,
)
from gdm.distribution.controllers import (
    PeakShavingBaseLoadingControlSetting,
    VoltVarControlSetting,
    InverterController,
)
from gdm.distribution.enums import Phase
from gdm.quantities import (
    ReactivePower,
    ActivePower,
)


def test_distribution_battery_without_controller():
    battery = DistributionBattery(
        name="test_battery",
        bus=DistributionBus.example(),
        phases=[Phase.A],
        equipment=BatteryEquipment.example(),
        inverter=InverterEquipment.example(),
        reactive_power=ReactivePower(1000, "var"),
        active_power=ActivePower(1000, "watt"),
        controller=None,
    )
    assert battery.controller is None
    # No exception should be raised


def test_distribution_solar_with_invalid_controller():
    # InverterController example should raise an excention given the controller uses SolarOnly control algorithm
    with pytest.raises(ValueError):
        inverter_control = InverterController.example()
        inverter_control.active_power_control = PeakShavingBaseLoadingControlSetting.example()
        DistributionSolar(
            name="test_battery",
            bus=DistributionBus.example(),
            phases=[Phase.A],
            equipment=BatteryEquipment.example(),
            inverter=InverterEquipment.example(),
            reactive_power=ReactivePower(1000, "var"),
            active_power=ActivePower(1000, "watt"),
            controller=inverter_control,
        )


def test_distribution_battery_with_controller():
    battery = DistributionBattery(
        name="test_battery",
        bus=DistributionBus.example(),
        phases=[Phase.A],
        equipment=BatteryEquipment.example(),
        inverter=InverterEquipment.example(),
        reactive_power=ReactivePower(1000, "var"),
        active_power=ActivePower(1000, "watt"),
        controller=InverterController(
            name="inv1",
            active_power_control=PeakShavingBaseLoadingControlSetting.example(),
            reactive_power_control=VoltVarControlSetting.example(),
            prioritize_active_power=False,
            night_mode=True,
        ),
    )
    assert isinstance(battery.controller, InverterController)
    # No exception should be raised


def test_distribution_battery_example():
    battery = DistributionBattery.example()
    assert battery.name == "battery1"
    assert isinstance(battery.bus, DistributionBus)
    assert battery.phases == [Phase.A, Phase.B, Phase.C]
    assert isinstance(battery.equipment, BatteryEquipment)
    assert isinstance(battery.inverter, InverterEquipment)
    assert isinstance(battery.reactive_power, ReactivePower)
    assert isinstance(battery.active_power, ActivePower)
    assert isinstance(battery.controller, InverterController)


def test_distribution_battery_aggregate():
    batteries = [
        DistributionBattery(
            name="battery_1",
            bus=DistributionBus.example(),
            phases=[Phase.A],
            equipment=BatteryEquipment.example(),
            inverter=InverterEquipment.example(),
            reactive_power=ReactivePower(1500, "var"),
            active_power=ActivePower(3000, "watt"),
            controller=None,
        ),
        DistributionBattery(
            name="battery_2",
            bus=DistributionBus.example(),
            phases=[Phase.A],
            equipment=BatteryEquipment.example(),
            inverter=InverterEquipment.example(),
            reactive_power=ReactivePower(500, "var"),
            active_power=ActivePower(1000, "watt"),
            controller=None,
        ),
    ]
    aggregated_battery = DistributionBattery.aggregate(
        batteries, bus=DistributionBus.example(), name="aggregated_battery", split_phase_mapping={}
    )

    assert aggregated_battery.equipment.discharging_efficiency == 98
    assert aggregated_battery.equipment.charging_efficiency == 98
    assert aggregated_battery.equipment.idling_efficiency == 99
    assert aggregated_battery.equipment.rated_energy.to("Wh").magnitude == 8000
    assert aggregated_battery.equipment.rated_power.to("watt").magnitude == 2000
    assert aggregated_battery.inverter.rated_apparent_power.to("va").magnitude == 7600
    assert aggregated_battery.inverter.dc_to_ac_efficiency == 100
    assert aggregated_battery.reactive_power.to("var").magnitude == 2000
    assert aggregated_battery.active_power.to("watt").magnitude == 4000
