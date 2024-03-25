"""This module contains curve interface."""

from typing import Annotated

from pydantic import model_validator, Field
from infrasys.component_models import Component


class Curve(Component):
    """An interface for representing a curve using x and y points. e.g for volt-var and volt-watt curves."""

    curve_x: Annotated[list[float], Field(..., description="The x values of the curve")]

    curve_y: Annotated[list[float], Field(..., description="The y values of the curve")]

    @model_validator(mode="after")
    def validate_fields(self) -> "Curve":
        if len(self.curve_x) != len(self.curve_y):
            msg = f"curve_x ({self.curve_x=}) and curve_y ({self.curve_y=}) have different lengths"
            raise ValueError(msg)
        return self

    @classmethod
    def example(cls) -> "Curve":
        """Example of a Curve (Volt-Var IEEE-1547 standard)."""
        return Curve(
            curve_x=[0.5, 0.92, 0.98, 1.02, 1.08, 1.5], curve_y=[1.0, 1.0, 0.0, 0.0, -1.0, -1.0]
        )

    @classmethod
    def vv_vw_example(cls) -> "Curve":
        """Example of a Curve (Volt-Var Volt-Watt IEEE-1547 standard)."""
        return Curve(curve_x=[0.5, 1.06, 1.1, 1.5], curve_y=[1.0, 1.0, 0.0, 0.0])
