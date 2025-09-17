
from typing import Annotated
from pydantic import BaseModel, Field

from gdm.structural.enumerations import (
    EquipmentType,
    DimensionLengthUnits,
)

class BaseDimension(BaseModel):
    dimension_length : Annotated[float, Field(description="The dimension of the equipment. Can be length, width or height")]
    units: Annotated[DimensionLengthUnits, Field(description="unit for the dimension length")]

class BaseEquipment(BaseModel):
    equipment_id: Annotated[str, Field(min_length=10, max_length=40, description="Equipment identifier.")]
    equipment_type: Annotated[EquipmentType, Field(description="Equipment type")]
    weight_in_pounds: Annotated[float, Field(description="The weight of the equipment in pounds")]
    unit_cost_in_usd: Annotated[float, Field(description="The cost of the equipment in USD")]