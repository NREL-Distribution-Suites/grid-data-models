"""This module contains cost model interface."""

import datetime
from enum import Enum
from typing import Annotated, Optional


from pydantic import (
    PlainSerializer,
    PositiveFloat,
    ConfigDict,
    model_validator,
)
from infrasys import Component


class OperatingUnitEnum(str, Enum):
    """Operating unit enumeration."""

    KWH = "kWh"
    HOUR = "hr"
    KW = "kW"
    KVA = "kVA"


class CostModel(Component):
    """Data model for base cost."""

    purchase_date: Annotated[
        datetime.datetime, PlainSerializer(lambda x: x.strftime("%Y-%m-%d %H:%M:%S"))
    ]
    capital_dollars: PositiveFloat
    operating_dollars: Optional[PositiveFloat] = None
    operating_unit: Optional[OperatingUnitEnum] = None
    labor_dollars: Optional[PositiveFloat] = None
    name: str = ""
    notes: Optional[str] = None
    location: Optional[str] = None
    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=False)

    @model_validator(mode="after")
    def validate_fields(self) -> "CostModel":
        """Custom validator for cost fields."""
        if self.operating_dollars is not None and self.operating_unit is None:
            msg = "Operating unit can not be null when operating dollar is specified"
            raise ValueError(msg)
        return self

    @classmethod
    def example(cls) -> "CostModel":
        """Example for cost model."""
        return CostModel(
            purchase_date=datetime.datetime.now(datetime.timezone.utc), capital_dollars=234.45
        )
