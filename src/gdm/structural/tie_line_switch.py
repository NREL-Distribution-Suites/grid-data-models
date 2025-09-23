from typing import Literal, Annotated, Optional
from infrasys import Component
from pydantic import Field, field_validator
from gdm.structural.base_classes import BaseEquipment, BaseDimension

from gdm.structural.enumerations import (
    EquipmentType,
    MountingTypesLVSwitch,
    MountingTypesMVSwitch,
    SwitchingSequence,
    SwitchPoleConfiguration,
    SwitchOperatingMechanism,
    NEMARating
    )

class TieLineSwitch(BaseEquipment):
    equipment_type: Annotated[Literal[EquipmentType.TIE_LINE_SWITCH], Field(description="Equipment type") ] = EquipmentType.TIE_LINE_SWITCH
    pole_configuration: Annotated[SwitchPoleConfiguration | None, Field(description="Pole configuration of the tie-line switch")]
    switching_sequence: Annotated[SwitchingSequence | None, Field(description="Switching sequence of the tie-line switch")]
    voltage_rating: Annotated[float | None, Field(description="Voltage rating of the tie-line switch in kV")]
    current_rating: Annotated[float | None, Field(description="Current rating of the tie-line switch in Amperes")]
    interrupting_rating: Annotated[Optional[float] | None, Field(description="Interrupting rating (kAIC) of the tie-line switch in kA")]
    number_of_phases: Annotated[int | None, Field(description="Number of phases in the tie-line switch (1 for single-phase, 3 for three-phase)")]
    operating_mechanism: Annotated[SwitchOperatingMechanism | None, Field(description="Operating mechanism of the tie-line switch")]
    mounting_type_LV: Annotated[MountingTypesLVSwitch | None, Field(description="Mounting type of the LV tie-line switch")]
    mounting_type_MV: Annotated[MountingTypesMVSwitch | None, Field(description="Mounting type of the MV tie-line switch")]
    NEMA_rating: Annotated[Optional[NEMARating], Field(description="NEMA rating of the tie-line switch")] 
    IP_rating: Annotated[Optional[int], Field(description="Insert the number of the IP rating of the tie-line switch (e.g., 54 for IP54)")]
    
    height: Annotated[BaseDimension | None, Field(description="Height of the tie-line switch")]
    width: Annotated[BaseDimension | None, Field(description="Width of the tie-line switch")]
    depth: Annotated[BaseDimension | None, Field(description="Depth of the tie-line switch")]
    weight_in_pounds: Annotated[float | None, Field(description="The weight of the equipment in pounds")]

    @field_validator("mounting_type_LV", "mounting_type_MV", always=True)
    def check_mounting_type(cls, v, values, field):
        if values.get("voltage_rating") is not None:
            if values["voltage_rating"] <= 1 and field.name == "mounting_type_MV" and v is not None:
                raise ValueError("Mounting type for MV tie-line switch should not be provided for voltage ratings <= 1 kV")
            if values["voltage_rating"] > 1 and field.name == "mounting_type_LV" and v is not None:
                raise ValueError("Mounting type for LV tie-line switch should not be provided for voltage ratings > 1 kV")
        return v

    @field_validator("NEMA_rating", "IP_rating", always=True)
    def check_ratings(cls, v, values):
        voltage = values.get("voltage_rating")
        mounting_lv = values.get("mounting_type_LV")
        mounting_mv = values.get("mounting_type_MV")
        
        # Determine the relevant mounting type based on voltage
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

class BaseTieLineSwitch(Component):
    electrical_properties: None
    physical_properties: Annotated[TieLineSwitch | None , Field(description="Physical properties of the tie line switch")]