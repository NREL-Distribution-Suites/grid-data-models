from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated

from infrasys import Component
from infrasys.location import Location
from pydantic import Field

from gdm.quantities import PositiveActivePower, PositiveDistance, PositiveWeight


class PoleMaterial(str, Enum):
    ALUMINUM = "ALUMINUM"
    ALUMINUM_DAVIT = "ALUMINUM_DAVIT"
    FIBERGLASS = "FIBERGLASS"
    GALVANIZED_DAVIT = "GALVANIZED_DAVIT"
    GALVANIZED = "GALVANIZED"
    STEEL_DAVIT_PRIMED = "STEEL_DAVIT_PRIMED"
    STEEL_DAVIT = "STEEL_DAVIT"
    STEEL_STANDARD_PRIMED = "STEEL_STANDARD_PRIMED"
    WOOD_TREATED = "WOOD_TREATED"
    WOOD_HARD = "WOOD_HARD"
    WOOD_SALT_TREATED = "WOOD_SALT_TREATED"
    WOOD_SOFT = "WOOD_SOFT"
    CONCRETE = "CONCRETE"
    WOOD = "WOOD"
    STEEL = "STEEL"
    COMPOSITE = "COMPOSITE"
    STEEL_TUBULAR = "STEEL_TUBULAR"
    IRON = "IRON"
    OTHER = "OTHER"


class PoleClassification(str, Enum):
    CLASS_1 = "1"
    CLASS_2 = "2"
    CLASS_3 = "3"
    CLASS_4 = "4"
    CLASS_5 = "5"
    CLASS_6 = "6"
    CLASS_7 = "7"
    CLASS_H1 = "H1"
    CLASS_H2 = "H2"
    OTHER = "OTHER"


class FoundationType(str, Enum):
    DIRECT_EMBEDMENT = "DIRECT_EMBEDMENT"
    ANCHOR = "ANCHOR"


class GuyWireMaterial(str, Enum):
    GALVANIZED_STEEL = "GALVANIZED_STEEL"
    STAINLESS_STEEL = "STAINLESS_STEEL"


class CrossArmMaterial(str, Enum):
    FIBERGLASS = "FIBERGLASS"
    TREATED_WOOD = "TREATED_WOOD"
    STEEL = "STEEL"
    COMPOSITE = "COMPOSITE"
    ALUMINUM = "ALUMINUM"


class CrossArmType(str, Enum):
    HORIZONTAL = "HORIZONTAL"
    VSHAPED = "VSHAPED"
    DOUBLE = "DOUBLE"
    SIDEARM = "SIDEARM"


class CrossArm(Component):
    """Interface for cross arm."""

    material: Annotated[CrossArmMaterial, Field(..., description="Cross arm material.")]
    weight: Annotated[PositiveWeight, Field(..., description="Weight of cross arm.")]
    arm_type: Annotated[CrossArmType, Field(..., description="Cross arm type used for the pole.")]
    height: Annotated[PositiveDistance, Field(..., description="Height from the ground.")]


class RoundedPoleDimension(Component):
    """Interface for rounded dimension of pole."""

    ground_diameter: Annotated[
        PositiveDistance, Field(..., description="Pole diameter at the ground.")
    ]
    tip_diameter: Annotated[PositiveDistance, Field(..., description="Pole diameter at the tip.")]


class CrossSectionalPoleDimension(Component):
    """Interface for rounded dimension of pole."""

    ground_width: Annotated[
        PositiveDistance, Field(..., description="Pole ground width dimension.")
    ]
    tip_width: Annotated[PositiveDistance, Field(..., description="Pole tip width dimension.")]
    ground_depth: Annotated[
        PositiveDistance, Field(..., description="Pole ground depth dimension.")
    ]
    tip_depth: Annotated[PositiveDistance, Field(..., description="Pole tip depth dimension.")]


class TreeTrimming(Component):
    trimming_cycle: Annotated[timedelta, Field(..., description="How often tree is trimmed.")]
    last_time_trimmed: Annotated[
        datetime, Field(..., description="Last time tree is trimmed for this pole.")
    ]


class StreetLight(Component):
    power_rating: Annotated[
        PositiveActivePower, Field(..., description="Power rating of the light.")
    ]


class ElectricPole(Component):
    """Interface for electric pole."""

    material: Annotated[PoleMaterial, Field(..., description="Pole material type.")]
    height: Annotated[
        PositiveDistance,
        Field(..., description="Height of the pole including undergrounded portion."),
    ]
    dimension: Annotated[
        RoundedPoleDimension | CrossSectionalPoleDimension,
        Field(..., description="Pole dimension."),
    ]
    foundation_type: Annotated[FoundationType, Field(..., description="Type of foundation used.")]
    foundation_depth: Annotated[PositiveDistance, Field(..., description="Depth of foundation.")]
    installed_date: Annotated[datetime, Field(..., description="When the pole was installed.")]
    classification: Annotated[PoleClassification, Field(..., description="Pole class.")]
    weight: Annotated[PositiveWeight, Field(..., description="Total weight of the pole.")]
    num_of_guy_wires: Annotated[
        int, Field(..., description="Number of guy wires attached to the pole.")
    ]
    cross_arm: Annotated[
        list[CrossArm], Field(..., description="Cross arm model for electric pole.")
    ]
    trimming: Annotated[
        TreeTrimming | None, Field(None, description="Tree trimming applicable or not.")
    ]
    street_lights: Annotated[
        list[StreetLight], Field([], description="Street lights attached to this pole.")
    ]
    elevation: Annotated[PositiveDistance, Field(..., description="Elevation from sea level.")]
    location: Annotated[Location, Field(..., description="Location of the pole.")]
