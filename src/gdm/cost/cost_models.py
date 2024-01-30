from datetime import datetime
from enum import Enum
from typing import Annotated, Optional
from gdm.distribution.distribution_model import BreakerArrangment

from pydantic import (
    BaseModel,
    PlainSerializer,
    PositiveFloat,
    ConfigDict,
    PositiveInt,
    confloat,
    model_validator,
)
from infrasys.quantities import Distance
from gdm.quantities import (
    PositiveApparentPower,
    PositiveCurrent,
    PositiveReactivePower,
    PositiveVoltage,
)


class OperatingUnitEnum(str, Enum):
    KWH = "kWh"
    HOUR = "hr"
    KW = "kW"
    KVA = "kVA"


class BaseCost(BaseModel):
    """Interface for base cost model."""

    id: Optional[int] = None
    purchase_date: Annotated[datetime, PlainSerializer(lambda x: x.strftime("%Y-%m-%d %H:%M:%S"))]
    capital_dollars: PositiveFloat
    operating_dollars: Optional[PositiveFloat] = None
    operating_unit: Optional[OperatingUnitEnum] = None
    labor_dollars: Optional[PositiveFloat] = None
    name: Optional[str] = None
    notes: Optional[str] = None
    country: Optional[str] = None
    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=False)

    @model_validator(mode="after")
    def validate_fields(self) -> "BaseCost":
        if self.operating_dollars is not None and self.operating_unit is None:
            msg = "Operating unit can not be null when operating dollar is specified"
            raise ValueError(msg)

    @classmethod
    def example(cls) -> "BaseCost":
        return BaseCost(purchase_date=datetime.utcnow(), capital_dollars=234.45)


class TransInstallEnum(str, Enum):
    POLE_MOUNT = "Pole Mount"
    PAD_MOUNT = "Pad Mount"
    UNDERGROUND = "Underground"


class VoltageType(str, Enum):
    LINE_TO_LINE = "Line to Line"
    LINE_TO_GROUND = "Line to Ground"


serializer = PlainSerializer(lambda x: f"{x.magnitude} {x.units}")


class TransformerCost(BaseCost):
    """Interface for transformer cost model."""

    voltage_type: VoltageType
    rated_ht_voltage: Annotated[PositiveVoltage, serializer]
    rated_lt_voltage: Annotated[PositiveVoltage, serializer]
    num_phases: PositiveInt
    install_type: TransInstallEnum
    capacity: Annotated[PositiveApparentPower, serializer]

    @classmethod
    def example(cls) -> "TransformerCost":
        return TransformerCost(
            purchase_date=datetime.utcnow(),
            capital_dollars=2345.32,
            voltage_type=VoltageType.LINE_TO_LINE,
            rated_ht_voltage=PositiveVoltage(12.47, "kilovolt"),
            rated_lt_voltage=PositiveVoltage(0.4, "kilovolt"),
            num_phases=3,
            install_type=TransInstallEnum.PAD_MOUNT,
            capacity=PositiveApparentPower(25, "kilova"),
        )


class ConductorCost(BaseCost):
    """Interface for conductor cost."""

    voltage_type: VoltageType
    rated_voltage: Annotated[PositiveVoltage, serializer]
    ampacity: Annotated[PositiveCurrent, serializer]
    length: Annotated[Distance, serializer]
    num_phases: PositiveInt

    @classmethod
    def example(cls) -> "ConductorCost":
        return ConductorCost(
            capital_dollars=3456.56,
            purchase_date=datetime.utcnow(),
            num_phases=3,
            voltage_type=VoltageType.LINE_TO_GROUND,
            rated_voltage=PositiveVoltage(12.47, "kilovolt"),
            ampacity=PositiveCurrent(90, "ampere"),
            length=Distance(34.0, "meter"),
        )


class CableCost(ConductorCost):
    """Interface for cable cost."""

    @classmethod
    def example(cls) -> "CableCost":
        return CableCost(
            capital_dollars=3456.6,
            purchase_date=datetime.utcnow(),
            voltage_type=VoltageType.LINE_TO_LINE,
            rated_voltage=PositiveVoltage(12.47, "kilovolt"),
            ampacity=PositiveCurrent(90, "ampere"),
            length=Distance(55.0, "meter"),
            num_phases=3,
        )


class RecloserCost(ConductorCost):
    """Interface for recloser cost."""

    @classmethod
    def example(cls) -> "RecloserCost":
        return RecloserCost(
            capital_dollars=3456.6,
            purchase_date=datetime.utcnow(),
            voltage_type=VoltageType.LINE_TO_LINE,
            rated_voltage=PositiveVoltage(12.47, "kilovolt"),
            ampacity=PositiveCurrent(90, "ampere"),
            length=Distance(55.0, "meter"),
            num_phases=3,
        )


class SwitchCost(ConductorCost):
    """Interface for recloser cost."""

    @classmethod
    def example(cls) -> "SwitchCost":
        return SwitchCost(
            capital_dollars=3456.6,
            purchase_date=datetime.utcnow(),
            voltage_type=VoltageType.LINE_TO_LINE,
            rated_voltage=PositiveVoltage(12.47, "kilovolt"),
            ampacity=PositiveCurrent(90, "ampere"),
            length=Distance(55.0, "meter"),
            num_phases=3,
        )


class FuseCost(ConductorCost):
    """Interface for recloser cost."""

    @classmethod
    def example(cls) -> "FuseCost":
        return FuseCost(
            capital_dollars=3456.6,
            purchase_date=datetime.utcnow(),
            voltage_type=VoltageType.LINE_TO_LINE,
            rated_voltage=PositiveVoltage(12.47, "kilovolt"),
            ampacity=PositiveCurrent(90, "ampere"),
            length=Distance(55.0, "meter"),
            num_phases=3,
        )


class VoltageRegulatorCost(BaseCost):
    """Interface for voltage regulator cost."""

    voltage_type: VoltageType
    rated_voltage: Annotated[PositiveVoltage, serializer]
    num_phases: PositiveInt
    install_type: TransInstallEnum
    capacity: Annotated[PositiveApparentPower, serializer]

    @classmethod
    def example(cls) -> "VoltageRegulatorCost":
        return VoltageRegulatorCost(
            purchase_date=datetime.utcnow(),
            capital_dollars=2345.32,
            voltage_type=VoltageType.LINE_TO_LINE,
            rated_voltage=PositiveVoltage(12.47, "kilovolt"),
            num_phases=3,
            install_type=TransInstallEnum.PAD_MOUNT,
            capacity=PositiveApparentPower(25, "kilova"),
        )


class CapacitorCost(BaseCost):
    """Interface to capacitor cost."""

    voltage_type: VoltageType
    rated_voltage: Annotated[PositiveVoltage, serializer]
    num_phases: PositiveInt
    install_type: TransInstallEnum
    capacity: Annotated[PositiveReactivePower, serializer]

    @classmethod
    def example(cls) -> "CapacitorCost":
        return CapacitorCost(
            purchase_date=datetime.utcnow(),
            capital_dollars=2345.32,
            voltage_type=VoltageType.LINE_TO_LINE,
            rated_voltage=PositiveVoltage(12.47, "kilovolt"),
            num_phases=3,
            install_type=TransInstallEnum.PAD_MOUNT,
            capacity=PositiveReactivePower(25, "kilovar"),
        )


class SubstationCost(BaseCost):
    """Interface for substation cost."""

    capacity: Annotated[PositiveApparentPower, serializer]
    hv_breaker_arrangement: BreakerArrangment
    lv_breaker_arrangement: BreakerArrangment

    @classmethod
    def example(cls) -> "SubstationCost":
        return SubstationCost(
            capital_dollars=100000.0,
            purchase_date=datetime.utcnow(),
            hv_breaker_arrangement=BreakerArrangment.BREAKER_AND_A_HALF,
            lv_breaker_arrangement=BreakerArrangment.BREAKER_AND_A_HALF,
            capacity=PositiveApparentPower(500, "megava"),
        )


class FeederConstructionEnum(str, Enum):
    OVERHEAD = "Overhead"
    UNDERGROUND = "Underground"
    HYBRID = "Hybrid"


class FeederLocTypeEnum(str, Enum):
    RURAL = "RURAL"
    URBAN = "URBAN"


class FeederCost(BaseCost):
    """Interface for feeder cost."""

    length: Annotated[Distance, serializer]
    construction: FeederConstructionEnum
    category: FeederLocTypeEnum
    ug_to_overhead_ratio: confloat(ge=0, le=1)

    @classmethod
    def example(cls) -> "FeederCost":
        return FeederCost(
            capital_dollars=100000.0,
            purchase_date=datetime.utcnow(),
            length=Distance(4.5, "kilometer"),
            construction=FeederConstructionEnum.OVERHEAD,
            category=FeederLocTypeEnum.URBAN,
            ug_to_overhead_ratio=0.0,
        )
