""" This module contains interface for powersystem load."""

from typing import Annotated

from infrasys import Component
from infrasys.quantities import ActivePower
from pydantic import model_validator, Field

from gdm.quantities import ReactivePower
from gdm.constants import PINT_SCHEMA


class PowerSystemLoad(Component):
    """Interface for power system load.
    Uses ZIP model where real power is:
    P = P_0[ a_p (|V|/V_0)^2 + b_p (|V|/V_0) + c_p]
    and reactive power is:
    Q = Q_0[ a_q (|V|/V_0)^2 + b_q (|V|/V_0) + c_q]
    """
    real_power: Annotated[
            ActivePower,
            PINT_SCHEMA,
            Field(
                default=ActivePower(0,"kilowatt"),
                description="Base real power for the ZIP model. (P_0) ",
            ),
    ]
    reactive_power: Annotated[
            ReactivePower,
            PINT_SCHEMA,
            Field(
                default=ReactivePower(0,"kilovar"),
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

    @model_validator(mode="after")
    def validate_fields(self) -> "PowerSystemLoad":
        """Sum of ZIP parameters should be 1 for both P and Q"""
        real_sum = self.z_real + self.i_real + self.p_real 
        if not real_sum == 1: 
            msg = f"Sum of ZIP parameters z_real: {self.z_real}, i_real: {self.i_real}, p_real: {self.p_real} is {real_sum} not 1"
            raise ValueError(msg)
        imag_sum = self.z_imag + self.i_imag + self.p_imag 
        if not imag_sum == 1: 
            msg = f"Sum of ZIP parameters z_imag: {self.z_imag}, i_imag: {self.i_imag}, p_imag: {self.p_imag} is {imag_sum} not 1"
            raise ValueError(msg)
        return self

    @classmethod
    def example(cls) -> "PowerSystemLoad":
        return PowerSystemLoad(
            real_power = ActivePower(2.5, "kilowatt"),
            reactive_power = ReactivePower(0, "kilovar"),
            z_real=0.75,
            z_imag=1.0,
            i_real=0.1,
            i_imag=0.0,
            p_real=0.15,
            p_imag=0.0,
            name="PhaseLoad1",
        )
