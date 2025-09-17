from typing import Literal, Annotated, Optional
from pydantic import Field, field_validator
from infrasys import Component
from gdm.structural.base_classes import BaseEquipment, BaseDimension

from gdm.structural.enumerations import (
    EquipmentType,
    MountingTypesLVFuses,
    MountingTypesMVFuses,
    HousingMaterial,
    FuseTimeCurrentCharacteristic,
    FuseClasses,
    FuseTypes,
    NEMARating
    )

# Voltage and interrupting rating limitations for LV fuses based on fuse class
FuseClass_Limitations = {
    FuseClasses.CLASS_CC: {"voltage": [0.6], "interrupting_kA": [200], "current_limiting": True},
    FuseClasses.CLASS_J: {"voltage": [0.6], "interrupting_kA": [200], "current_limiting": True},
    FuseClasses.CLASS_H: {"voltage": [0.25, 0.6], "interrupting_kA": [10], "current_limiting": False},
    FuseClasses.CLASS_K5: {"voltage": [0.25, 0.6], "interrupting_kA": [50, 100, 200], "current_limiting": False},
    FuseClasses.CLASS_L: {"voltage": [0.6], "interrupting_kA": [50, 100, 200], "current_limiting": True},
    FuseClasses.CLASS_T: {"voltage": [0.3, 0.6], "interrupting_kA": [200], "current_limiting": True},
    FuseClasses.RK1: {"voltage": [0.25, 0.6], "interrupting_kA": [200], "current_limiting": True},
    FuseClasses.RK5: {"voltage": [0.25, 0.6], "interrupting_kA": [200], "current_limiting": True},
}

class Fuse(BaseEquipment):
    equipment_type: Annotated[Literal[EquipmentType.FUSE], Field(description="Equipment type") ] = EquipmentType.FUSE
    fuse_type: Annotated[FuseTypes | None, Field(description="Type of the fuse (e.g., Expulsion, Cutout, Cartridge, etc.)")]
    current_limiting: Annotated[bool | None, Field(description="Indicates if the fuse is current limiting")]
    voltage_rating: Annotated[float | None, Field(description="Voltage rating of the fuse in kV")]
    current_rating: Annotated[float | None, Field(description="Current rating of the fuse in Amperes")]
    interrupting_rating: Annotated[float | None, Field(description="Interrupting rating (kAIC) of the fuse in kA")]
    time_current_characteristic: Annotated[FuseTimeCurrentCharacteristic | None, Field(description="Time-current characteristic of the fuse")]
    fuse_class: Annotated[Optional[FuseClasses] | None, Field(description="Fuse class of LV (e.g., Class H, Class K, Class T, etc.)")]
    number_of_poles: Annotated[int | None, Field(description="Number of poles of the fuse (e.g., 1, 2, 3)")]
    mounting_type_LV: Annotated[MountingTypesLVFuses | None, Field(description="Mounting type of the LV fuse")]
    mounting_type_MV: Annotated[MountingTypesMVFuses | None, Field(description="Mounting type of the MV fuse")]
    housing_material: Annotated[HousingMaterial | None, Field(description="Housing material of the fuse")]
    NEMA_rating: Annotated[NEMARating | None, Field(description="NEMA rating of the fuse (e.g., NEMA 1, NEMA 3R, NEMA 4X)")]
    IP_rating: Annotated[int | None, Field(description="Insert the number of the IP rating of the fuse (e.g., 54 for IP54)")]

    height: Annotated[BaseDimension | None, Field(description="Height of the fuse")]
    width: Annotated[BaseDimension | None, Field(description="Width of the fuse")]
    depth: Annotated[BaseDimension | None, Field(description="Depth of the fuse")]
    weight_in_pounds: Annotated[float | None, Field(description="The weight of the equipment in pounds")]

    @field_validator("fuse_class", always=True)     # validate voltage and interrupting ratings based on fuse class for LV fuses
    def validate_class(cls, v, values):
        voltage_rating = values.get('voltage_rating')
        interrupting_rating = values.get('interrupting_rating')
        current_limiting = values.get('current_limiting')
        data = FuseClass_Limitations.get(v)

        if voltage_rating not in data["voltage"] and v is not None:
            raise ValueError("Voltage rating not valid for selected fuse class")
        if interrupting_rating  not in data["interrupting_kA"] and v is not None:
            raise ValueError("Interrupting rating not valid for selected fuse class")
        if current_limiting != data["current_limiting"] and v is not None:
            raise ValueError("Current limiting flag doesn't match fuse class")
        return v
        
    @field_validator("mounting_type_LV", "mounting_type_MV", always=True)
    def check_mounting_type(cls, v, values, field):
        if values.get("voltage_rating") is not None:
            if values["voltage_rating"] <= 1 and field.name == "mounting_type_MV" and v is not None:
                raise ValueError("Mounting type for MV fuse should not be provided for voltage ratings <= 1 kV")
            if values["voltage_rating"] > 1 and field.name == "mounting_type_LV" and v is not None:
                raise ValueError("Mounting type for LV fuse should not be provided for voltage ratings > 1 kV")
        return v
    
class BaseFuse(Component):
    electrical_properties: None
    physical_properties: Annotated[Fuse | None , Field(description="Physical properties of the fuse")]