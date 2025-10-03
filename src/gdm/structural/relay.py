from typing import Literal, Annotated, Optional
from pydantic import Field, field_validator
from infrasys import Component
from gdm.structural.base_classes import BaseEquipment, BaseDimension

from gdm.structural.enumerations import (
    EquipmentType,
    NEMARating,
    ProtectionRelayMountingTypes,
    ProtectionRelayTypes,
    ProtectionRelayOperatingPrinciple,
    RelayCommunicationProtocols,
    RelayContactConfiguration
    )

class Relay(BaseEquipment):
    equipment_type: Annotated[Literal[EquipmentType.RELAY], Field(description="Equipment type") ] = EquipmentType.RELAY
    relay_type: Annotated[ProtectionRelayTypes | None, Field(description="Type of relay")]
    number_of_phases: Annotated[int | None, Field(description="Number of phases the relay monitors (1 for single-phase, 3 for three-phase)")]
    number_of_protection_elements: Annotated[int | None, Field(description="Number of protection elements in the relay")]
    voltage_rating: Annotated[float | None, Field(description="Voltage rating of the relay in kV")]
    current_rating: Annotated[float | None, Field(description="Current rating of the relay in Amperes")]
    operating_principle: Annotated[ProtectionRelayOperatingPrinciple | None, Field(description="Operating principle of the relay")]
    communication_protocols: Annotated[RelayCommunicationProtocols | None, Field(description="Communication protocols supported by the relay")]
    contact_configuration: Annotated[Optional[RelayContactConfiguration] | None, Field(description="Contact configuration of the relay")]
    mounting_type: Annotated[ProtectionRelayMountingTypes | None, Field(description="Mounting type of the relay")]
    time_delay_settings: Annotated[float | None, Field(description="Time delay settings of the relay in seconds")]
    NEMA_rating: Annotated[Optional[NEMARating] | None, Field(description="NEMA rating of the relay (e.g., NEMA 1, NEMA 3R, NEMA 4X)")]
    IP_rating: Annotated[Optional[int] | None, Field(description="Insert the number of the IP rating of the relay (e.g., 54 for IP54)")]

    height: Annotated[BaseDimension | None, Field(description="Height of the relay")]
    width: Annotated[BaseDimension | None, Field(description="Width of the relay")]
    depth: Annotated[BaseDimension | None, Field(description="Depth of the relay")]
    weight_in_pounds: Annotated[float | None, Field(description="The weight of the equipment in pounds")]


    @field_validator("NEMA_rating", "IP_rating", always=True)
    def check_enclosure_rating(cls, v, values):
        if values.get("mounting_type") == "Panel-Mounted" and values.get("voltage_rating", 0) > 1:
            if v is None:
                raise ValueError("Panel-mounted MV relays must have NEMA/IP rating")
        return v

class BaseRelay(Component):
    electrical_properties: None
    physical_properties: Annotated[Relay | None , Field(description="Physical properties of the relay")]
