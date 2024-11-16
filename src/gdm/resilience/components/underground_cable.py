from typing import Annotated
from infrasys import Component
from pydantic import Field


class UndergroundCable(Component):
    power_system_resource_name: Annotated[
        str, Field(..., description="Name of branch used in power system model.")
    ]
