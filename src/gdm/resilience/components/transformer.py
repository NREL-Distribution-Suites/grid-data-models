from typing import Annotated
from infrasys import Component
from pydantic import Field

from gdm.quantities import PositiveDistance


class BaseTransformer(Component):
    power_system_resource_name: Annotated[
        str, Field(..., description="Name used in power system model.")
    ]


class PoleMountedTransformer(BaseTransformer):
    mounting_height: Annotated[
        PositiveDistance, Field(..., description="Mounting height from ground.")
    ]
