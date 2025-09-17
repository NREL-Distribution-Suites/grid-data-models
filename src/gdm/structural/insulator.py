from typing import Literal, Annotated
from pydantic import BaseModel, field_validator, Field
from infrasys import Component
from gdm.structural.base_classes import BaseEquipment, BaseDimension

from gdm.structural.enumerations import (
    EquipmentType,
    HousingMaterial
    )

class PinInsulator(BaseModel):
    cantilever_strength: Annotated[float | None, Field(description="Cantilever strength of the insulator in kN")]

class SuspensionInsulator(BaseModel):
    tensile_strength: Annotated[float | None, Field(description="Tensile/failing load strength of the insulator in kN")]

class StrainInsulator(BaseModel):
    tensile_strength: Annotated[float | None, Field(description="Tensile/failing load strength of the insulator in kN")]

class ShackleInsulator(BaseModel):
    tensile_strength: Annotated[float | None, Field(description="Tensile/failing load strength of the insulator in kN")]

class LinePostInsulator(BaseModel):
    cantilever_strength: Annotated[float | None, Field(description="Cantilever strength of the insulator in kN")]

class StationPostInsulator(BaseModel):
    cantilever_strength: Annotated[float | None, Field(description="Cantilever strength of the insulator in kN")]

class Insulator(BaseEquipment):
    equipment_type: Annotated[Literal[EquipmentType.INSULATOR], Field(description="Equipment type") ] = EquipmentType.INSULATOR
    insulator_type: Annotated[PinInsulator, SuspensionInsulator, StrainInsulator, ShackleInsulator | None, Field(description="Type of insulator (e.g., Pin, Suspension, Strain, Shackle)")]
    material: Annotated[HousingMaterial | None, Field(description="Material of the insulator (e.g., Porcelain, Glass, Polymer)")]
    voltage_rating: Annotated[float | None, Field(description="Voltage rating of the insulator in kV")]
    creepage_distance: Annotated[BaseDimension | None, Field(description="Creepage distance of the insulator in mm/kV")]

    diameter: Annotated[BaseDimension | None, Field(description="Diameter of the insulator")]
    height: Annotated[BaseDimension | None, Field(description="Height of the insulator")]
    weight_in_pounds: Annotated[float | None, Field(description="The weight of the equipment in pounds")]

class BaseInsulator(Component):
    electrical_properties: None
    physical_properties: Annotated[Insulator | None , Field(description="Physical properties of the insultator")]
