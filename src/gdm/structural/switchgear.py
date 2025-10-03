from typing import Literal, Annotated, Optional
from pydantic import field_validator, Field
from infrasys import Component
from gdm.structural.base_classes import BaseEquipment, BaseDimension

from gdm.structural.enumerations import (
    EquipmentType,
    SwitchgearTypes,
    MountingTypesLVSwitch,
    MountingTypesMVSwitch,
    NEMARating,
    SwitchgearInsulationMedium,
    SwitchgearBusConfig,
    SwitchgearControlTypes,
    CircuitBreakerOperatingMechanism
    )

class Switchgear(BaseEquipment):
    equipment_type: Annotated[Literal[EquipmentType.SWITCHGEAR], Field(description="Equipment type") ] = EquipmentType.SWITCHGEAR
    gear_type: Annotated[SwitchgearTypes | None, Field(description="Type of switchgear")]
    voltage_rating: Annotated[float | None, Field(description="Voltage rating of the switchgear in kV")]
    current_rating: Annotated[float | None, Field(description="Current rating of the switchgear in Amperes")]
    interrupting_rating: Annotated[float | None, Field(description="Interrupting rating (kAIC) of the switchgear in kA")]
    mounting_type_LV: Annotated[MountingTypesLVSwitch | None, Field(description="Mounting type of the LV switchgear")]
    mounting_type_MV: Annotated[MountingTypesMVSwitch | None, Field(description="Mounting type of the MV switchgear")]
    number_of_phases: Annotated[int | None, Field(description="Number of phases in the switchgear (1 for single-phase, 3 for three-phase)")]
    number_of_bays: Annotated[int | None, Field(description="Number of bays in the switchgear")]
    insulation_medium: Annotated[SwitchgearInsulationMedium | None, Field(description="Insulation medium of the switchgear")]
    bus_configuration: Annotated[SwitchgearBusConfig | None, Field(description="Bus configuration of the switchgear")]
    control_voltage: Annotated[float | None, Field(description="Auxiliary (control) voltage of the switchgear in Volts")]
    control_options: Annotated[SwitchgearControlTypes | None, Field(description="Control options available for the switchgear")]
    breaker_operating_mechanism: Annotated[CircuitBreakerOperatingMechanism | None, Field(description="Operating mechanism of the circuit breakers within the switchgear")]
    NEMA_rating: Annotated[Optional[NEMARating] | None, Field(description="NEMA rating of the switchgear")]
    IP_rating: Annotated[Optional[int] | None, Field(description="Insert the number of the IP rating of the switchgear (e.g., 54 for IP54)")]

    height: Annotated[BaseDimension | None, Field(description="Height of the switchgear")]
    width: Annotated[BaseDimension | None, Field(description="Width of the switchgear")]
    depth: Annotated[BaseDimension | None, Field(description="Depth of the switchgear")]
    weight_in_pounds: Annotated[float | None, Field(description="The weight of the equipment in pounds")]

    @field_validator("mounting_type_LV", "mounting_type_MV", always=True)
    def check_mounting_type(cls, v, values, field):
        if values.get("voltage_rating") is not None:
            if values["voltage_rating"] <= 1 and field.name == "mounting_type_MV" and v is not None:
                raise ValueError("Mounting type for MV disconnect switch should not be provided for voltage ratings <= 1 kV")
            if values["voltage_rating"] > 1 and field.name == "mounting_type_LV" and v is not None:
                raise ValueError("Mounting type for LV disconnect switch should not be provided for voltage ratings > 1 kV")
        return v
    
    @field_validator("control_voltage", always=True)
    def check_aux_voltage(cls, v, values):
        main_v = values.get("voltage_rating")
        if main_v is not None and v is not None and v >= main_v:
            raise ValueError("Control voltage must be less than the main voltage rating")
        return v
    
    @field_validator("bus_configuration", always=True)
    def check_bus_config(cls, v, values):
        phases = values.get("number_of_phases")
        if v is not None and phases is not None:
            if phases == 1 and v != SwitchgearBusConfig.SINGLE_BUS:
                raise ValueError(f"{v} configuration is only valid for three-phase switchgear")
        return v
    
class BaseSwitchgear(Component):
    electrical_properties: None
    physical_properties: Annotated[Switchgear | None , Field(description="Physical properties of the switchgear")]
