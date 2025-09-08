from typing import Literal, Annotated
from pydantic import BaseModel, Field

from gdm.structural.enumerations import (
    EquipmentType,
    DimensionLengthUnits,
    MountingTypesFuses,
    HousingMaterial,
    FuseTimeCurrentCharacteristic,
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

class Fuse(BaseEquipment):
    equipment_type: Annotated[Literal[EquipmentType.FUSE], Field(description="Equipment type") ] = EquipmentType.FUSE
    voltage_rating: Annotated[float | None, Field(description="Voltage rating of the fuse in kV")]
    current_rating: Annotated[float | None, Field(description="Current rating of the fuse in Amperes")]
    interrupting_rating: Annotated[float | None, Field(description="Interrupting rating (kAIC) of the fuse in kA")]
    time_current_characteristic: Annotated[FuseTimeCurrentCharacteristic | None, Field(description="Time-current characteristic of the fuse")]
    mounting_type: Annotated[MountingTypesFuses | None, Field(description="Mounting type of the fuse")]
    housing_material: Annotated[HousingMaterial | None, Field(description="Housing material of the fuse")]
    NEMA_rating: Annotated[NEMARating | None, Field(description="NEMA rating of the fuse (e.g., NEMA 1, NEMA 3R, NEMA 4X)")]
    IP_rating: Annotated[int | None, Field(description="Insert the number of the IP rating of the fuse (e.g., 54 for IP54)")]

    height: Annotated[BaseDimension | None, Field(description="Height of the fuse")]
    width: Annotated[BaseDimension | None, Field(description="Width of the fuse")]
    depth: Annotated[BaseDimension | None, Field(description="Depth of the fuse")]
    weight_in_pounds: Annotated[float | None, Field(description="The weight of the equipment in pounds")]
