"""This module contains phase load equipment."""

from typing import Annotated, Optional
import uuid
from infrasys import Component

from pydantic import model_validator, PositiveInt, Field

from gdm.quantities import ActivePower, ReactivePower
from gdm.constants import PINT_SCHEMA


class PhaseLoadEquipment(Component):
    """Data model for single phase load equipment."""

    real_power: Annotated[
        ActivePower,
        PINT_SCHEMA,
        Field(
            default=ActivePower(0, "kilowatt"),
            description="Base real power for the ZIP model. (P_0) ",
        ),
    ]
    reactive_power: Annotated[
        ReactivePower,
        PINT_SCHEMA,
        Field(
            default=ReactivePower(0, "kilovar"),
            description="Base reactive power for the ZIP model. (Q_0) ",
        ),
    ]
    z_real: Annotated[
        float,
        Field(
            description="Constant impedance zip load real component. (a_p)",
        ),
    ]
    z_imag: Annotated[
        float,
        Field(
            description="Constant impedance zip load imaginary component. (a_q)",
        ),
    ]
    i_real: Annotated[
        float,
        Field(
            description="Constant current zip load real component. (b_p)",
        ),
    ]
    i_imag: Annotated[
        float,
        Field(
            description="Constant current zip load imaginary component. (b_q)",
        ),
    ]
    p_real: Annotated[
        float,
        Field(
            description="Constant power zip load real component. (c_p)",
        ),
    ]
    p_imag: Annotated[
        float,
        Field(
            description="Constant power zip load imaginary component. (c_q)",
        ),
    ]
    num_customers: Annotated[
        Optional[PositiveInt],
        Field(None, description="Number of customers for this load"),
    ]
    min_voltage_pu: Annotated[
        float | None,
        Field(None, ge=0, description="Voltage below which the load uses constant impedance."),
    ]
    max_voltage_pu: Annotated[
        float | None,
        Field(None, gt=0, description="Voltage above which the load uses constant impedance."),
    ]
    cutoff_voltage_pu: Annotated[
        float, Field(0.0, ge=0, description="Voltage below which the ZIP load draws no power.")
    ]
    active_power_voltage_exponent: Annotated[
        float | None,
        Field(None, description="Exponent in P=P0*(V/V0)^exponent, overriding real ZIP terms."),
    ]
    reactive_power_voltage_exponent: Annotated[
        float | None,
        Field(
            None, description="Exponent in Q=Q0*(V/V0)^exponent, overriding reactive ZIP terms."
        ),
    ]

    @classmethod
    def split(cls, instance: "PhaseLoadEquipment", num_splits: int) -> "PhaseLoadEquipment":
        return instance.model_copy(
            update={
                "name": str(uuid.uuid4()),
                "real_power": instance.real_power / num_splits,
                "reactive_power": instance.reactive_power / num_splits,
            }
        )

    @classmethod
    def aggregate(cls, instances: list["PhaseLoadEquipment"], name: str) -> "PhaseLoadEquipment":
        behavior = {}
        for field in (
            "min_voltage_pu",
            "max_voltage_pu",
            "cutoff_voltage_pu",
            "active_power_voltage_exponent",
            "reactive_power_voltage_exponent",
        ):
            values = {getattr(instance, field) for instance in instances}
            if len(values) > 1:
                raise ValueError(f"Cannot aggregate phase loads with different {field}.")
            if values:
                behavior[field] = values.pop()
        z_real_sum = sum([inst.real_power * inst.z_real for inst in instances]) or ActivePower(
            0, "watt"
        )
        z_imag_sum = sum(
            [inst.reactive_power * inst.z_imag for inst in instances]
        ) or ReactivePower(0, "var")
        p_real_sum = sum([inst.real_power * inst.p_real for inst in instances]) or ActivePower(
            0, "watt"
        )
        p_imag_sum = sum(
            [inst.reactive_power * inst.p_imag for inst in instances]
        ) or ReactivePower(0, "var")
        i_real_sum = sum([inst.real_power * inst.i_real for inst in instances]) or ActivePower(
            0, "watt"
        )
        i_imag_sum = sum(
            [inst.reactive_power * inst.i_imag for inst in instances]
        ) or ReactivePower(0, "var")
        new_real = (z_real_sum + p_real_sum + i_real_sum) or ActivePower(0, "watt")
        new_react = (z_imag_sum + p_imag_sum + i_imag_sum) or ReactivePower(0, "var")

        def weighted_factor(sum_component, total_power, unit):
            return (
                (sum_component.to(unit) / total_power.to(unit)).magnitude
                if total_power.magnitude
                else 0
            )

        return PhaseLoadEquipment(
            name=name,
            real_power=new_real,
            reactive_power=new_react,
            z_real=weighted_factor(z_real_sum, new_real, "watt"),
            z_imag=weighted_factor(z_imag_sum, new_react, "var"),
            p_real=weighted_factor(p_real_sum, new_real, "watt"),
            p_imag=weighted_factor(p_imag_sum, new_react, "var"),
            i_real=weighted_factor(i_real_sum, new_real, "watt"),
            i_imag=weighted_factor(i_imag_sum, new_react, "var"),
            num_customers=sum(filter(None, [inst.num_customers for inst in instances])) or None,
            **behavior,
        )

    @model_validator(mode="after")
    def validate_fields(self) -> "PhaseLoadEquipment":
        """Sum of ZIP parameters should be 1 for both P and Q"""
        if (
            self.min_voltage_pu is not None
            and self.max_voltage_pu is not None
            and self.min_voltage_pu > self.max_voltage_pu
        ):
            raise ValueError("min_voltage_pu must not exceed max_voltage_pu.")
        if (self.active_power_voltage_exponent is None) != (
            self.reactive_power_voltage_exponent is None
        ):
            raise ValueError("Both voltage exponents must be specified together.")
        if self.active_power_voltage_exponent is not None and self.cutoff_voltage_pu:
            raise ValueError("Voltage cutoff is only supported for ZIP loads.")
        real_sum = self.z_real + self.i_real + self.p_real
        if self.real_power.magnitude and real_sum != 1:
            msg = f"Sum of ZIP parameters z_real: {self.z_real}, i_real: {self.i_real}, p_real: {self.p_real} is {real_sum} not 1"
            raise ValueError(msg)
        imag_sum = self.z_imag + self.i_imag + self.p_imag
        if self.reactive_power and imag_sum != 1:
            msg = f"Sum of ZIP parameters z_imag: {self.z_imag}, i_imag: {self.i_imag}, p_imag: {self.p_imag} is {imag_sum} not 1"
            raise ValueError(msg)
        return self

    @classmethod
    def example(cls) -> "PhaseLoadEquipment":
        return PhaseLoadEquipment(
            real_power=ActivePower(2.5, "kilowatt"),
            reactive_power=ReactivePower(0, "kilovar"),
            z_real=0.75,
            z_imag=1.0,
            i_real=0.1,
            i_imag=0.0,
            p_real=0.15,
            p_imag=0.0,
            name="PhaseLoad1",
        )
