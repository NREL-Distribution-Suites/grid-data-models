from typing import Literal, Annotated, Optional
from infrasys import Component
from pydantic import Field, field_validator
from gdm.structural.base_classes import BaseEquipment, BaseDimension

from gdm.structural.enumerations import (
    EquipmentType,
    MountingTypesLVSwitch,
    MountingTypesMVSwitch,
    SwitchingSequence,
    InsulationMedium,
    DisconnectSwitchTypes,
    SwitchOperatingMechanism,
    SwitchPoleConfiguration,
    NEMARating
    )

class DisconnectSwitch(BaseEquipment):
    equipment_type: Annotated[Literal[EquipmentType.DISCONNECT_SWITCH], Field(description="Equipment type") ] = EquipmentType.DISCONNECT_SWITCH
    switch_type: Annotated[DisconnectSwitchTypes | None, Field(description="Type of disconnect switch")]
    number_of_phases: Annotated[int | None, Field(description="Number of phases in the disconnect switch (1 for single-phase, 3 for three-phase)")]
    voltage_rating: Annotated[float | None, Field(description="Voltage rating of the disconnect switch in kV")]
    current_rating: Annotated[float | None, Field(description="Current rating of the disconnect switch in Amperes")]
    interrupting_rating: Annotated[float | None, Field(description="Interrupting rating (kAIC) of the disconnect switch in kA")]
    creepage_distance: Annotated[float | None, Field(description="Creepage distance of the disconnect switch in mm")]
    fused: Annotated[bool | None, Field(description="Indicates whether the disconnect switch is fused (True) or not (False)")]
    operating_mechanism: Annotated[SwitchOperatingMechanism | None, Field(description="Operating mechanism of the disconnect switch")]
    pole_configuration: Annotated[SwitchPoleConfiguration | None, Field(description="Pole configuration of the disconnect switch")]
    mounting_type_LV: Annotated[MountingTypesLVSwitch | None, Field(description="Mounting type of the LV disconnect switch")]
    mounting_type_MV: Annotated[MountingTypesMVSwitch | None, Field(description="Mounting type of the MV disconnect switch")]
    insulation_medium: Annotated[InsulationMedium | None, Field(description="Insulation medium of the disconnect switch")]
    switching_sequence: Annotated[Optional[SwitchingSequence] | None, Field(description="Switching sequence of the disconnect switch")]
    NEMA_rating: Annotated[Optional[NEMARating], Field(description="NEMA rating of the disconnect switch")]
    IP_rating: Annotated[Optional[int], Field(description="Insert the number of the IP rating of the disconnect switch (e.g., 54 for IP54)")] 

    height: Annotated[BaseDimension | None, Field(description="Height of the disconnect switch")]
    width: Annotated[BaseDimension | None, Field(description="Width of the disconnect switch")]
    depth: Annotated[BaseDimension | None, Field(description="Depth of the disconnect switch")]
    weight_in_pounds: Annotated[float | None, Field(description="The weight of the equipment in pounds")]
    
    @field_validator("mounting_type_LV", "mounting_type_MV", always=True)
    def check_mounting_type(cls, v, values, field):
        if values.get("voltage_rating") is not None:
            if values["voltage_rating"] <= 1 and field.name == "mounting_type_MV" and v is not None:
                raise ValueError("Mounting type for MV disconnect switch should not be provided for voltage ratings <= 1 kV")
            if values["voltage_rating"] > 1 and field.name == "mounting_type_LV" and v is not None:
                raise ValueError("Mounting type for LV disconnect switch should not be provided for voltage ratings > 1 kV")
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
    
    @field_validator("switching_sequence", always=True)
    def check_switching_sequence(cls, v, values):
        if v is not None and values.get("pole_configuration") == SwitchPoleConfiguration.SINGLE_POLE:
            raise ValueError("Switching sequence does not apply to single pole disconnect switches")

class BaseDisconnectSwitch(Component):
    electrical_properties: None
    physical_properties: Annotated[DisconnectSwitch | None, Field(description="Physical properties of the disconnect switch")]