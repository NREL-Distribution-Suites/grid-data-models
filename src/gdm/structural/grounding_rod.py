from typing import Literal, Annotated, Optional
from infrasys import Component
from pydantic import BaseModel, Field, field_validator
from gdm.structural.base_classes import BaseEquipment, BaseDimension

from gdm.structural.enumerations import (
    EquipmentType,
    GroundRodMaterial,
    GroundRodInstallationType
    )

class Rod(BaseModel):
    rod_length: Annotated[float | None, Field(description="Length of the grounding rod in meters")]
    rod_diameter: Annotated[float | None, Field(description="Diameter of the grounding rod in mm")]
    installation_type: Annotated[Optional[GroundRodInstallationType] | None, Field(description="Installation type of the grounding rod")]

class Plate(BaseModel):
    plate_length: Annotated[float | None, Field(description="Length of the grounding plate in mm")]
    plate_width: Annotated[float | None, Field(description="Width of the grounding plate in mm")]
    plate_thickness: Annotated[float | None, Field(description="Thickness of the grounding plate in mm")]

class Ufer(BaseModel):
    concrete_cover_thickness: Annotated[float | None, Field(description="Concrete cover thickness of the Ufer grounding in mm")]
    rebar_diameter: Annotated[float | None, Field(description="Diameter of the rebar used in Ufer grounding in mm")]
    rebar_length: Annotated[float | None, Field(description="Length of the rebar used in Ufer grounding in meters")]

class GroundingRod(BaseEquipment):
    equipment_type: Annotated[Literal[EquipmentType.GROUNDING_ROD], Field(description="Equipment type") ] = EquipmentType.GROUNDING_ROD
    type: Annotated[Rod | Plate | Ufer | None, Field(description="Type of grounding rod")]
    material: Annotated[Optional[GroundRodMaterial] | None, Field(description="Material of the grounding rod")]

    height: Annotated[BaseDimension | None, Field(description="Height of the grounding rod")]
    width: Annotated[BaseDimension | None, Field(description="Width of the grounding rod")]
    depth: Annotated[BaseDimension | None, Field(description="Depth of the grounding rod")]
    weight_in_pounds: Annotated[float | None, Field(description="The weight of the equipment in pounds")]

class BaseGroundingRod(Component):
    electrical_properties: None
    physical_properties: Annotated[GroundingRod | None, Field(description="Physical properties of the grounding rod")]