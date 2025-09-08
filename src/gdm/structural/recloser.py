from typing import Literal, Annotated
from pydantic import BaseModel, field_validator, Field

from gdm.structural.enumerations import (
    EquipmentType,
    DimensionLengthUnits,
    InsulationMedium,
    TrippingCurves, 
    RecloserControlTypes,
    MountingTypesLV, 
    MountingTypesMV, 
    RecloserOperatingDutyCycles,
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
 
class Recloser(BaseEquipment):
    equipment_type: Annotated[Literal[EquipmentType.RECLOSER], Field(description="Equipment type") ] = EquipmentType.RECLOSER
    voltage_class: Annotated[float | None, Field(description="Voltage class of the recloser in kV")]
    number_of_phases: Annotated[int | None, Field(description="Number of phases in the recloser (1 for single-phase, 3 for three-phase)")]
    continuous_current_rating: Annotated[float | None, Field(description="Continuous current rating of the recloser in kA")]
    interrupting_rating: Annotated[float | None, Field(description="Interrupting rating of the recloser in kA")]
    interrupting_medium: Annotated[InsulationMedium | None, Field(description="Interrupting medium of the recloser")]
    number_of_operations_at_interrupting_rating: Annotated[int | None, Field(description="Number of operations at interrupting rating")]
    trip_curve: Annotated[TrippingCurves | None, Field(description="Trip curve type of the recloser")]
    control_type: Annotated[RecloserControlTypes | None, Field(description="Control type of the recloser")]
    mounting_type_LV: Annotated[MountingTypesLV | None, Field(description="Mounting type for low voltage side of the recloser")]
    mounting_type_MV: Annotated[MountingTypesMV | None, Field(description="Mounting type for medium voltage side of the recloser")]
    withstand_voltage_dry: Annotated[float | None, Field(description="Withstand voltage in dry conditions in kV")]
    withstand_voltage_wet: Annotated[float | None, Field(description="Withstand voltage in wet conditions in kV")]
    operating_duty_cycle: Annotated[RecloserOperatingDutyCycles | None, Field(description="Operating duty cycle of the recloser")]
    NEMA_rating: Annotated[NEMARating | None, Field(description="NEMA rating of the recloser (e.g., NEMA 1, NEMA 3R, NEMA 4X)")]
    IP_rating: Annotated[int | None, Field(description="Insert the number of the IP rating of the recloser (e.g., 54 for IP54)")]

    height: Annotated[BaseDimension | None, Field(description="Height of the recloser")]
    width: Annotated[BaseDimension | None, Field(description="Width of the recloser")]
    depth: Annotated[BaseDimension | None, Field(description="Depth of the recloser")]
    weight_in_pounds: Annotated[float | None, Field(description="The weight of the equipment in pounds")]

    @field_validator("mounting_type_LV", "mounting_type_MV", always=True)
    def check_mounting_type(cls, v, values, field):
        if values.get("voltage_rating") is not None:
            if values["voltage_rating"] <= 1 and field.name == "mounting_type_MV" and v is not None:
                raise ValueError("Mounting type for MV recloser should not be provided for voltage ratings <= 1 kV")
            if values["voltage_rating"] > 1 and field.name == "mounting_type_LV" and v is not None:
                raise ValueError("Mounting type for LV recloser should not be provided for voltage ratings > 1 kV")
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