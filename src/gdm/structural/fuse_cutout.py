from typing import Literal, Annotated, Optional
from infrasys import Component
from pydantic import Field, field_validator
from gdm.structural.base_classes import BaseEquipment, BaseDimension

from gdm.structural.enumerations import (
    EquipmentType,
    FuseCutoutTypes,
    FuseCutoutStyle,
    HousingMaterial,
    FuseCutoutLinkTypes,
    InsulationMedium,
    FuseCutoutMountingTypes,
    FuseCutoutTimeCurrentCharacteristic,
    NEMARating
    )

class FuseCutout(BaseEquipment):
    equipment_type: Annotated[Literal[EquipmentType.FUSE_CUTOUT], Field(description="Equipment type") ] = EquipmentType.FUSE_CUTOUT
    cutout_fuse_type: Annotated[FuseCutoutTypes | None, Field(description="Type of fuse cutout")]
    cutout_style: Annotated[FuseCutoutStyle | None, Field(description="Style of the fuse cutout")]
    voltage_rating: Annotated[float | None, Field(description="Voltage rating of the fuse cutout in kV")]
    current_rating: Annotated[float | None, Field(description="Current rating of the fuse cutout in Amperes")]
    interrupting_rating: Annotated[float | None, Field(description="Interrupting rating (kAIC) of the fuse cutout in kA")]
    impulse_voltage_rating: Annotated[float | None, Field(description="Impulse voltage rating (BIL) of the fuse cutout in kV")]
    power_frequency_withstand_voltage_dry: Annotated[Optional[float] | None, Field(description="Power-frequency withstand voltage in dry conditions in kV")]
    power_frequency_withstand_voltage_wet: Annotated[Optional[float] | None, Field(description="Power-frequency withstand voltage in wet conditions in kV")]
    creepage_distance: Annotated[float | None, Field(description="Creepage distance of the fuse cutout in mm")]
    pigtail_length: Annotated[Optional[float] | None, Field(description="Length of the pigtail in mm")]
    housing_material: Annotated[HousingMaterial | None, Field(description="Housing material of the fuse cutout")]
    MV_link_type: Annotated[Optional[FuseCutoutLinkTypes] | None, Field(description="Time-current characteristic of the MV fuse cutout")]
    insulation_medium: Annotated[Optional[InsulationMedium] | None, Field(description="Insulation medium of the fuse cutout")]
    LV_time_current_characteristic: Annotated[Optional[FuseCutoutTimeCurrentCharacteristic] | None, Field(description="Time-current characteristic of the LV fuse cutout")]
    mounting_type: Annotated[Optional[FuseCutoutMountingTypes] | None, Field(description="Mounting type of the fuse cutout")] = FuseCutoutMountingTypes.POLE_MOUNTED
    NEMA_rating: Annotated[Optional[NEMARating], Field(description="NEMA rating of the fuse cutout")]
    IP_rating: Annotated[Optional[int], Field(description="Insert the number of the IP rating of the fuse cutout (e.g., 54 for IP54)")]

    height: Annotated[BaseDimension | None, Field(description="Height of the fuse cutout")]
    width: Annotated[BaseDimension | None, Field(description="Width of the fuse cutout")]
    depth: Annotated[BaseDimension | None, Field(description="Depth of the fuse cutout")]
    weight_in_pounds: Annotated[float | None, Field(description="The weight of the equipment in pounds")]

    @field_validator("mounting_type", always=True)
    def check_mounting_type(cls, v, values):
        if v == FuseCutoutMountingTypes.POLE_MOUNTED:
            if values.get("NEMA_rating") is not None or values.get("IP_rating") is not None:
                raise ValueError("NEMA/IP rating does not apply to pole-mounted fuse cutouts")
        return v
    
    @field_validator("MV_link_type", always=True)
    def check_mv_link_type(cls, v, values):
        if values.get("voltage_rating") is not None and values["voltage_rating"] <= 1 and v is not None:
            raise ValueError("MV link type should only be provided for MV fuse cutouts (voltage rating > 1 kV)")
        return v

    @field_validator("LV_time_current_characteristic", always=True)
    def check_time_current_characteristic(cls, v, values):
        if values.get("voltage_rating") is not None and values["voltage_rating"] > 1 and v is not None:
            raise ValueError("Time-current characteristic should only be provided for LV fuse cutouts (voltage rating <= 1 kV)")
        return v      
    
class BaseFuseCutout(Component):
    electrical_properties: None
    physical_properties: Annotated[FuseCutout | None, Field(description="Physical properties of the fuse cutout")]