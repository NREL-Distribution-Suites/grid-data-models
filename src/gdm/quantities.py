from infrasys.base_quantity import BaseQuantity, ureg
from infrasys.quantities import Current, Distance, Resistance, Voltage


ureg.define("var = ampere * volt")
ureg.define("va = ampere * volt")


class ReactivePower(BaseQuantity):
    __compatible_unit__ = "var"


class PositiveReactivePower(ReactivePower):
    def __init__(self, value, units, **kwargs):
        assert value > 0, f"Reactive power ({value}, {units}) must be positive."


class PositiveDistance(Distance):
    def __init__(self, value, units, **kwargs):
        assert value > 0, f"Distance ({value}, {units}) must be positive."


class ApparentPower(BaseQuantity):
    __compatible_unit__ = "va"


class PositiveApparentPower(ApparentPower):
    def __init__(self, value, units, **kwargs):
        assert value > 0, f"Apparent power ({value}, {units}) must be positive."


class Percentage(BaseQuantity):
    __compatible_unit__ = "dimensionless"


class PerUnit(BaseQuantity):
    __compatible_unit__ = "dimensionless"


class Capacitance(BaseQuantity):
    __compatible_unit__ = "farad"


class PositiveCapacitance(Capacitance):
    def __init__(self, value, units, **kwargs):
        assert value > 0, f"Capacitance ({value}, {units}) must be positive."


class PositiveResistance(Resistance):
    def __init__(self, value, units, **kwargs):
        assert value >= 0, f"Resistance ({value}, {units}) must be positive."


class Reactance(Resistance):
    pass


class PositiveReactance(PositiveResistance):
    def __init__(self, value, units, **kwargs):
        assert value > 0, f"Reactance ({value}, {units}) must be positive."


class PositiveCurrent(Current):
    def __init__(self, value, units, **kwargs):
        assert value > 0, f"Current ({value}, {units}) must be positive."


class PositiveVoltage(Voltage):
    def __init__(self, value, units, **kwargs):
        assert value > 0, f"Voltage ({value}, {units}) must be positive."
