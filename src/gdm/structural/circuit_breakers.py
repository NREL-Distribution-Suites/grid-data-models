from typing import Literal, Annotated
from pydantic import BaseModel, Field

from gdm.structural.enumerations import (
    EquipmentType,
    DimensionLengthUnits,
    CircuitBreakerTypes,
    TrippingCurves, 
    CircuitBreakerOperatingMechanism,
    CircuitBreakerMountingType, 
    LocationType,
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

class ACCircuitBreaker(BaseModel):
    voltage_rating_ac: Annotated[float | None, Field(description="AC voltage rating of the circuit breaker in kV")]
    interrupting_rating_ac: Annotated[float | None, Field(description="AC interrupting rating (kAIC) of the circuit breaker in kA")]
    short_circuit_current_rating_ac: Annotated[float | None, Field(description=" AC short-circuit current (SCCR) rating of the circuit breaker in kA")]
    operating_current_ac: Annotated[float | None, Field(description="Rated line AC current (In) in Amperes")]

class DCCircuitBreaker(BaseModel):
    voltage_rating_dc: Annotated[float | None, Field(description="DC voltage rating of the circuit breaker in kV")] 
    interrupting_rating_dc: Annotated[float | None, Field(description="DC interrupting rating (kAIC) of the circuit breaker in kA")]
    short_circuit_current_rating_dc: Annotated[float | None, Field(description="DC short-circuit current (SCCR) rating of the circuit breaker in kA")]
    operating_current_dc: Annotated[float | None, Field(description="Rated line DC current (In) in Amperes")]

class DualCircuitBreaker(BaseModel):
    voltage_rating_ac: Annotated[float | None, Field(description="AC voltage rating of the circuit breaker in kV")]
    voltage_rating_dc: Annotated[float | None, Field(description="DC voltage rating of the circuit breaker in kV")] 
    interrupting_rating_dc: Annotated[float | None, Field(description="DC interrupting rating (kAIC) of the circuit breaker in kA")]
    interrupting_rating_ac: Annotated[float | None, Field(description="AC interrupting rating (kAIC) of the circuit breaker in kA")]
    short_circuit_current_rating_ac: Annotated[float | None, Field(description=" AC short-circuit current (SCCR) rating of the circuit breaker in kA")]
    short_circuit_current_rating_dc: Annotated[float | None, Field(description="DC short-circuit current (SCCR) rating of the circuit breaker in kA")]
    operating_current_ac: Annotated[float | None, Field(description="Rated line AC current (In) in Amperes")]
    operating_current_dc: Annotated[float | None, Field(description="Rated line DC current (In) in Amperes")]

class CircuitBreaker(BaseEquipment):
    equipment_type: Annotated[Literal[EquipmentType.CIRCUIT_BREAKER], Field(description="Equipment type") ] = EquipmentType.CIRCUIT_BREAKER
    breaker_type: Annotated[CircuitBreakerTypes | None, Field(description="Type of circuit breaker")] 
    trip_curve: Annotated[TrippingCurves | None, Field(description="Trip curve type of the circuit breaker")]
    operating_mechanism: Annotated[CircuitBreakerOperatingMechanism | None, Field(description="Operating mechanism of the circuit breaker (e.g., Spring, Hydraulic, Pneumatic)")]
    poles: Annotated[int | None, Field(description="Number of poles in the circuit breaker ")] 
    mounting_type: Annotated[CircuitBreakerMountingType | None, Field(description="Mounting type of the circuit breaker")]
    tripping_time: Annotated[float | None, Field(description="Tripping time of the circuit breaker in seconds")]
    voltage_rating: Annotated[DualCircuitBreaker | ACCircuitBreaker | DCCircuitBreaker | None, Field(description="Voltage rating of the circuit breaker (AC, DC, or Dual)")]
    location: Annotated[LocationType | None, Field(description="Location of the circuit breaker (Indoor or Outdoor)")]
    NEMA_rating: Annotated[NEMARating | None, Field(description="NEMA rating of the circuit breaker (e.g., NEMA 1, NEMA 3R, NEMA 4X)")]
    IP_rating: Annotated[int | None, Field(description="Insert the number of the IP rating of the circuit breaker (e.g., 54 for IP54)")]
    certification: Annotated[bool | None, Field(description="Is the circuit breaker certified? (e.g., UL, IEC)")] 

    height: Annotated[BaseDimension | None, Field(description="Height of the circuit breaker")]
    width: Annotated[BaseDimension | None, Field(description="Width of the circuit breaker")]
    depth: Annotated[BaseDimension | None, Field(description="Depth of the circuit breaker")]
    weight_in_pounds: Annotated[float | None, Field(description="The weight of the equipment in pounds")]