from typing import Literal, Annotated
from pydantic import BaseModel, field_validator, Field

from gdm.structural.enumerations import (
    EquipmentType,
    DimensionLengthUnits,
    MountingTypesLV, 
    MountingTypesMV, 
    HousingMaterial,
    NEMARating
    )

class BaseDimension(BaseModel):
    dimension_length : Annotated[float, Field(description="The dimension of the equipment. Can be length, width or height")]
    units: Annotated[DimensionLengthUnits, Field(description="unit for the dimension length")]

class BaseEquipment(BaseModel):
    equipment_id: Annotated[str, Field(min_length=10, max_length=40, description="Equipment identifier.")]
    equipment_type: Annotated[EquipmentType, Field(description="Equipment type")]
    weight_in_pounds: Annotated[float, Field(description="The weight of the equipment in pounds")]
    unit_cost_in_usd: Annotated[float, Field(description="The cost of the equipment in USD")]

class SurgeArrester(BaseEquipment):
    equipment_type: Annotated[Literal[EquipmentType.SURGE_ARRESTER], Field(description="Equipment type") ] = EquipmentType.SURGE_ARRESTER
    voltage_rating: Annotated[float | None, Field(description="Voltage rating of the surge arrester in kV")]
    continuous_current_rating: Annotated[float | None, Field(description="Continuous current rating of the surge arrester in Amperes")]
    nominal_discharge_current_rating: Annotated[float | None, Field(description="Nominal discharge current rating of the surge arrester in kA")]
    maximum_discharge_current_rating: Annotated[float | None, Field(description="Maximum discharge current rating of the surge arrester in kA")]
    energy_rating: Annotated[float | None, Field(description="Energy rating of the surge arrester in kJ/kV")]
    protection_level: Annotated[float | None, Field(description="Protection level of the surge arrester in kV")]
    response_time: Annotated[float | None, Field(description="Response time of the surge arrester in nanoseconds")]
    mounting_type_LV: Annotated[MountingTypesLV | None, Field(description="Mounting type of the LV surge arrester")]
    mounting_type_MV: Annotated[MountingTypesMV | None, Field(description="Mounting type of the MV surge arrester")]
    housing_material: Annotated[HousingMaterial | None, Field(description="Housing material of the surge arrester")]
    NEMA_rating: Annotated[NEMARating | None, Field(description="NEMA rating of the surge arrester (e.g., NEMA 1, NEMA 3R, NEMA 4X)")]
    IP_rating: Annotated[int | None, Field(description="Insert the number of the IP rating of the surge arrester (e.g., 54 for IP54)")]

    height: Annotated[BaseDimension | None, Field(description="Height of the surge arrester")]
    width: Annotated[BaseDimension | None, Field(description="Width of the surge arrester")]
    depth: Annotated[BaseDimension | None, Field(description="Depth of the surge arrester")]
    weight_in_pounds: Annotated[float | None, Field(description="The weight of the equipment in pounds")]

    @field_validator("mounting_type_LV", "mounting_type_MV", always=True)
    def check_mounting_type(cls, v, values, field):
        if values.get("voltage_rating") is not None:
            if values["voltage_rating"] <= 1 and field.name == "mounting_type_MV" and v is not None:
                raise ValueError("Mounting type for MV surge arrester should not be provided for voltage ratings <= 1 kV")
            if values["voltage_rating"] > 1 and field.name == "mounting_type_LV" and v is not None:
                raise ValueError("Mounting type for LV surge arrester should not be provided for voltage ratings > 1 kV")
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