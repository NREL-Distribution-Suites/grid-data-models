from datetime import datetime
from typing import Annotated
from enum import Enum
from infrasys import Component, Location
from pydantic import Field

from gdm.quantities import PositiveDistance, PositiveWeight
from gdm.resilience.components.pole import Pole


class InsulationClass(str, Enum):
    NEMA_A = "NEMA_A"
    NEMA_B = "NEMA_B"
    NEMA_F = "NEMA_F"
    NEMA_H = "NEMA_H"
    NEMA_N = "NEMA_N"
    NEMA_R = "NEMA_R"
    NEMA_S = "NEMA_S"
    IEC_Y = "IEC_Y"
    IEC_E = "IEC_E"


class TransformerDimension(Component):
    length: Annotated[
        PositiveDistance,
        Field(..., description="Length of the transformer unit."),
    ]
    width: Annotated[
        PositiveDistance,
        Field(..., description="Width of the transformer unit."),
    ]
    height: Annotated[
        PositiveDistance,
        Field(..., description="Height of the transformer unit."),
    ]


class BaseTransformer(Component):
    power_system_resource_name: Annotated[
        str, Field(..., description="Name used in power system model.")
    ]
    installed_date: Annotated[datetime, Field(..., description="When the pole was installed.")]
    weight: Annotated[PositiveWeight, Field(..., description="Total weight of the pole.")]
    dimension: Annotated[
        TransformerDimension,
        Field(..., description="Physical dimension of the transformer."),
    ]
    location: Annotated[Location, Field(..., description="Location of the transformer.")]
    elevation: Annotated[PositiveDistance, Field(..., description="Elevation from sea level.")]
    insulation_class: Annotated[
        InsulationClass,
        Field(..., description="Insulation class for base transformer."),
    ]


class PoleMountedTransformer(BaseTransformer):
    mounting_height: Annotated[
        PositiveDistance, Field(..., description="Mounting height from ground.")
    ]
    pole: Annotated[
        Pole,
        Field(..., description="Pole to which this transformer is attached to."),
    ]


class PadMountTransformer(BaseTransformer):
    pass


class GroundVaultTransformer(BaseTransformer):
    pass
