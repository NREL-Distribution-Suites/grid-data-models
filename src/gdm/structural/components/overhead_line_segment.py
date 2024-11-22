from datetime import datetime
from typing import Annotated, Self
from pydantic import Field, model_validator

from gdm.structural.components.base import _InstalledDateBaseComponent
from gdm.structural.components.pole import CrossArm
from gdm.structural.components.transformer import (
    PadMountTransformer,
    PoleMountedTransformer,
)
from gdm.structural.components.underground_junction import UndergroundJunction


class OverheadLineSegment(_InstalledDateBaseComponent):
    power_system_resource_name: Annotated[
        str,
        Field(..., description="Name of branch used in power system model."),
    ]
    from_component: Annotated[
        CrossArm | PoleMountedTransformer | UndergroundJunction | PadMountTransformer,
        Field(
            ...,
            description="Cross arm or transformer to which this segment is connected from.",
        ),
    ]
    to_component: Annotated[
        CrossArm | PoleMountedTransformer | UndergroundJunction | PadMountTransformer,
        Field(
            ...,
            description="Cross arm or transformer to which this segment is connected to.",
        ),
    ]

    @model_validator(mode="after")
    def validate_component_types(self) -> Self:
        if isinstance(self.from_component, UndergroundJunction) and isinstance(
            self.to_component, UndergroundJunction
        ):
            msg = "From and to component can not both be UndergroundJunction."
            raise ValueError(msg)
        if isinstance(self.from_component, PadMountTransformer) and isinstance(
            self.to_component, PadMountTransformer
        ):
            msg = "From and to component can not both be pad mount transformer."
            raise ValueError(msg)
        if self.from_component.name == self.to_component.name:
            msg = f"{self.from_component.name=} and {self.to_component.name=} can not be the same."
            raise ValueError(msg)
        return self

    @classmethod
    def example(cls) -> Self:
        return OverheadLineSegment(
            name="Line1",
            installed_date=datetime(2001, 1, 1, 0, 0, 0),
            power_system_resource_name="line-1",
            from_component=CrossArm.example(),
            to_component=CrossArm.example().model_copy(update={"name": "Line1-to"}),
        )
