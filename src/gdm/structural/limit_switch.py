from typing import Literal, Annotated, Optional
from infrasys import Component
from pydantic import Field, field_validator, BaseModel
from gdm.structural.base_classes import BaseEquipment, BaseDimension

from gdm.structural.enumerations import (
    EquipmentType,
    MountingTypesLVSwitch,
    MountingTypesMVSwitch,
    LimitSwitchActuatorTypes,
    LimitSwitchOperationTypes,
    LimitSwitchHousingMaterial,
    LimitSwitchContactConfiguration,
    ProximityLimitSwitchOutputType,
    NEMARating
    )

class MechanicalLimitSwitch(BaseModel):
    torque_rating: Annotated[Optional[float] | None, Field(description="Torque rating of the mechanical limit switch in N")] 
    travel_to_operate: Annotated[Optional[float] | None, Field(description="Travel to operate of the mechanical limit switch in mm")]
    actuator_type: Annotated[LimitSwitchActuatorTypes | None, Field(description="Type of actuator for the limit switch")]
    mechanical_life: Annotated[Optional[int] | None, Field(description="Mechanical life of the mechanical limit switch in number of operations")]
    operation_type: Annotated[LimitSwitchOperationTypes | None, Field(description="Operation type of the limit switch")]
    contact_configuration: Annotated[Optional[LimitSwitchContactConfiguration] | None, Field(description="Contact configuration of the mechanical limit switch")]

class ElectromechanicalLimitSwitch(BaseModel):
    contact_configuration: Annotated[Optional[LimitSwitchContactConfiguration] | None, Field(description="Contact configuration of the electrical limit switch")]

class ProximityLimitSwitch(BaseModel):
    sensing_distance: Annotated[Optional[float] | None, Field(description="Sensing distance of the proximity limit switch in mm")]
    output_type: Annotated[Optional[ProximityLimitSwitchOutputType] | None, Field(description="Output type of the proximity limit switch")]
    response_time: Annotated[Optional[float] | None, Field(description="Response time of the proximity limit switch in ms")]
    contact_type_NO: Annotated[Optional[bool] | None, Field(description="Contact type of the proximity limit switch, select True for Normally Open (NO) or False for Normally Closed (NC)")]

class MagneticLimitSwitch(BaseModel):
    magnetic_field_strength: Annotated[Optional[float] | None, Field(description="Magnetic field strength of the magnetic limit switch in mT")]
    switching_distance: Annotated[Optional[float] | None, Field(description="Switching distance of the magnetic limit switch in mm")]
    output_type: Annotated[Optional[str] | None, Field(description="Output type of the magnetic limit switch (e.g., Reed, Hall Effect)")]
    contact_type_NO: Annotated[Optional[bool] | None, Field(description="Contact type of the magnetic limit switch, select True for Normally Open (NO) or False for Normally Closed (NC)")]

class LimitSwitch(BaseEquipment):
    equipment_type: Annotated[Literal[EquipmentType.LIMIT_SWITCH], Field(description="Equipment type") ] = EquipmentType.LIMIT_SWITCH
    switch_type: Annotated[MechanicalLimitSwitch | ElectromechanicalLimitSwitch | ProximityLimitSwitch | MagneticLimitSwitch | None, Field(description="Type of limit switch")]
    voltage_rating: Annotated[float | None, Field(description="Voltage rating of the limit switch in kV")]
    current_rating: Annotated[float | None, Field(description="Current rating of the limit switch in Amperes")]
    operation_type: Annotated[LimitSwitchOperationTypes | None, Field(description="Operation type of the limit switch")]
    number_of_poles: Annotated[int | None, Field(description="Number of poles in the limit switch")]
    mounting_type_LV: Annotated[MountingTypesLVSwitch | None, Field(description="Mounting type of the LV limit switch")]
    mounting_type_MV: Annotated[MountingTypesMVSwitch | None, Field(description="Mounting type of the MV limit switch")]
    housing_material: Annotated[Optional[LimitSwitchHousingMaterial] | None, Field(description="Housing material of the limit switch")]
    NEMA_rating: Annotated[Optional[NEMARating], Field(description="NEMA rating of the tie-line switch")]
    IP_rating: Annotated[Optional[int], Field(description="Insert the number of the IP rating of the tie-line switch (e.g., 54 for IP54)")] 

    height: Annotated[BaseDimension | None, Field(description="Height of the limit switch")]
    width: Annotated[BaseDimension | None, Field(description="Width of the limit switch")]
    depth: Annotated[BaseDimension | None, Field(description="Depth of the limit switch")]
    weight_in_pounds: Annotated[float | None, Field(description="The weight of the equipment in pounds")]

    @field_validator("mounting_type_LV", "mounting_type_MV", always=True)
    def check_mounting_type(cls, v, values, field):
        if values.get("voltage_rating") is not None:
            if values["voltage_rating"] <= 1 and field.name == "mounting_type_MV" and v is not None:
                raise ValueError("Mounting type for MV limit switch should not be provided for voltage ratings <= 1 kV")
            if values["voltage_rating"] > 1 and field.name == "mounting_type_LV" and v is not None:
                raise ValueError("Mounting type for LV limit switch should not be provided for voltage ratings > 1 kV")
        return v

    @field_validator("NEMA_rating", "IP_rating", always=True)
    def check_ratings(cls, v, values):
        voltage = values.get("voltage_rating")
        mounting_lv = values.get("mounting_type_LV")
        mounting_mv = values.get("mounting_type_MV")
        
        # Determine the "active" mounting type based on voltage
        if voltage is not None:
            if voltage <= 1:  
                active_mounting = mounting_lv
            else: 
                active_mounting = mounting_mv
        else:
            active_mounting = None

        if active_mounting in ["Indoor", "Pad-Mounted"] and v is None:
            raise ValueError("Indoor or pad-mounted equipment requires NEMA/IP rating")
        return v

class BaseLimitSwitch(Component):
    electrical_properties: None
    physical_properties: Annotated[LimitSwitch | None , Field(description="Physical properties of the limit switch")]