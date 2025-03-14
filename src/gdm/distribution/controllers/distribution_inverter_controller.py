""" This module contains interface for distribution inverter controllers."""

from typing import Annotated, Literal
from datetime import time

from infrasys import Component
from pydantic import Field

from gdm.distribution.controllers.base.inverter_controller_base import (
    ReactivePowerInverterControllerBase,
    ActivePowerInverterControllerBase,
)
from gdm.distribution.distribution_enum import ControllerSupport
from gdm.distribution.curve import Curve
from gdm.quantities import ActivePower, ActivePowerPUTime


class PowerfactorInverterController(ReactivePowerInverterControllerBase):
    """Interface for an Inverter Controller using powerfactor to determine power output."""

    power_factor: Annotated[
        float, Field(ge=-1, le=1, description="The power factor used for the controller.")
    ]
    supported_by: Literal[
        ControllerSupport.BATTERY_AND_SOLAR
    ] = ControllerSupport.BATTERY_AND_SOLAR

    @classmethod
    def example(cls) -> "PowerfactorInverterController":
        "Example of a Power Factor based Inverter controller"
        return PowerfactorInverterController(
            power_factor=0.95,
        )


class VoltVarInverterController(ReactivePowerInverterControllerBase):
    """Interface for a Volt-Var Inverter Controller."""

    volt_var_curve: Annotated[
        Curve, Field(..., description="The volt-var curve that is being applied.")
    ]
    var_follow: Annotated[
        bool,
        Field(
            ...,
            description="""Set to false if you want inverter reactive power
                        generation absorption to respect inverter status""",
        ),
    ]
    supported_by: Literal[
        ControllerSupport.BATTERY_AND_SOLAR
    ] = ControllerSupport.BATTERY_AND_SOLAR

    @classmethod
    def example(cls) -> "VoltVarInverterController":
        "Example of a Volt-Var Inverter Controller"
        return VoltVarInverterController(
            volt_var_curve=Curve.example(),
            var_follow=False,
        )


class VoltWattInverterController(ActivePowerInverterControllerBase):
    """Interface for a Volt-Var Inverter Controller."""

    volt_watt_curve: Annotated[
        Curve, Field(..., description="The volt-watt curve that is being applied.")
    ]
    supported_by: Literal[ControllerSupport.SOLAR_ONLY] = ControllerSupport.SOLAR_ONLY

    @classmethod
    def example(cls) -> "VoltWattInverterController":
        "Example of a Volt-Watt Inverter Controller"
        return VoltWattInverterController(
            volt_watt_curve=Curve(curve_x=[0.5, 1.06, 1.1, 1.5], curve_y=[1.0, 1.0, 0.0, 0.0]),
        )


class BatteryPeakShavingBaseLoadingController(ActivePowerInverterControllerBase):
    """Interface for battery peak shaving base loading controller."""

    supported_by: Literal[ControllerSupport.BATTERY_ONLY] = ControllerSupport.BATTERY_ONLY
    peak_shaving_target: Annotated[ActivePower, Field(..., description="The peak shaving target.")]
    base_loading_target: Annotated[ActivePower, Field(..., description="The base loading target.")]

    @classmethod
    def example(cls) -> "BatteryPeakShavingBaseLoadingController":
        "Example of a battery peak shaving base loading controller"
        return BatteryPeakShavingBaseLoadingController(
            peak_shaving_target=ActivePower(1000, "watt"),
            base_loading_target=ActivePower(2000, "watt"),
        )


class BatteryCapacityFirmingController(ActivePowerInverterControllerBase):
    """Interface for battery capacity firming controller."""

    supported_by: Literal[ControllerSupport.BATTERY_ONLY] = ControllerSupport.BATTERY_ONLY
    max_active_power_roc: Annotated[
        ActivePowerPUTime,
        Field(..., description="Maximum allowable rate of charge for active power."),
    ]
    min_active_power_roc: Annotated[
        ActivePowerPUTime,
        Field(..., description="Minimum allowable rate of charge for active power."),
    ]

    @classmethod
    def example(cls) -> "BatteryCapacityFirmingController":
        "Example of a battery capacity firming controller"
        return BatteryCapacityFirmingController(
            max_active_power_roc=ActivePowerPUTime(1000, "kilowatt/second"),
            min_active_power_roc=ActivePowerPUTime(1000, "kilowatt/second"),
        )


class BatteryTimeBaseController(ActivePowerInverterControllerBase):
    """Interface for battery capacity firming controller."""

    supported_by: Literal[ControllerSupport.BATTERY_ONLY] = ControllerSupport.BATTERY_ONLY
    charging_start_time: Annotated[
        time, Field(..., description="The time at which the battery starts charging.")
    ]
    charging_end_time: Annotated[
        time, Field(..., description="The time at which the battery stops charging.")
    ]
    discharging_start_time: Annotated[
        time, Field(..., description="The time at which the battery starts discharging.")
    ]
    discharging_end_time: Annotated[
        time, Field(..., description="The time at which the battery stops discharging.")
    ]
    charging_power: Annotated[
        ActivePower, Field(..., description="The power to charge the battery.")
    ]
    discharging_power: Annotated[
        ActivePower, Field(..., description="The power to discharge the battery.")
    ]

    @classmethod
    def example(cls) -> "BatteryTimeBaseController":
        "Example of a battery capacity firming controller"
        return BatteryTimeBaseController(
            charging_start_time=time(hour=10, minute=0),
            charging_end_time=time(hour=11, minute=0),
            discharging_start_time=time(hour=21, minute=0),
            discharging_end_time=time(hour=22, minute=0),
            charging_power=ActivePower(1000, "watt"),
            discharging_power=ActivePower(1000, "watt"),
        )


class BatterySelfConsumptionController(ActivePowerInverterControllerBase):

    """Interface for battery self consumption controller."""

    supported_by: Literal[ControllerSupport.BATTERY_ONLY] = ControllerSupport.BATTERY_ONLY

    @classmethod
    def example(cls) -> "BatterySelfConsumptionController":
        "Example of a battery self consumption controller"
        return BatterySelfConsumptionController()


class BatteryTimeOfUseController(ActivePowerInverterControllerBase):
    """Interface for battery time of use controller."""

    supported_by: Literal[ControllerSupport.BATTERY_ONLY] = ControllerSupport.BATTERY_ONLY
    tarriff: ...
    charging_power: Annotated[
        ActivePower, Field(..., description="The power to charge the battery after TOU window.")
    ]

    @classmethod
    def example(cls) -> "BatteryTimeOfUseController":
        "Example of a battery time of use controller"
        return BatteryTimeOfUseController(charging_power=ActivePower(1000, "watt"), tarriff=...)


class BatteryDemandChargeController(ActivePowerInverterControllerBase):
    """Interface for battery demand charge controller."""

    supported_by: Literal[ControllerSupport.BATTERY_ONLY] = ControllerSupport.BATTERY_ONLY
    tarriff: ...
    charging_power: Annotated[
        ActivePower,
        Field(..., description="The power to charge the battery after demand change window."),
    ]

    @classmethod
    def example(cls) -> "BatteryDemandChargeController":
        "Example of a battery demand charge controller"
        return BatteryDemandChargeController(charging_power=ActivePower(1000, "watt"), tarriff=...)


class InverterController(Component):
    """Interface for Inverter controllers that control active and reactive power."""

    name: Annotated[str, Field("", description="Name of the inverter controller.")]

    active_power_control: Annotated[
        ActivePowerInverterControllerBase | None,
        Field(
            None,
            description="Controller settings to control active power output of the inverter",
        ),
    ]

    reactive_power_control: Annotated[
        ReactivePowerInverterControllerBase | None,
        Field(
            None,
            description="Controller settings to control reactive power output of the inverter",
        ),
    ]

    prioritize_active_power: Annotated[
        bool, Field(..., description="If True, the controller tries to prioritize active power.")
    ]

    night_mode: Annotated[
        bool,
        Field(
            ...,
            description="If True, the controller controls reactive power even when there is no active power.",
        ),
    ]

    @classmethod
    def example(cls) -> "InverterController":
        "Example of a Volt-Watt Inverter Controller"
        return InverterController(
            name="inv1",
            active_power_control=VoltWattInverterController.example(),
            reactive_power_control=VoltVarInverterController.example(),
            prioritize_active_power=False,
            night_mode=True,
        )
