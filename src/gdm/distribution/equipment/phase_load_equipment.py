"""This module contains phase load equipment."""

from typing import Annotated, Optional

from pydantic import PositiveInt, Field

from gdm.load import PowerSystemLoad


class PhaseLoadEquipment(PowerSystemLoad):
    """Interface for single phase load equipment."""

    num_customers: Annotated[
        Optional[PositiveInt],
        Field(None, description="Number of customers for this load"),
    ]

    @classmethod
    def example(cls) -> "PhaseLoadEquipment":
        """Example for phase load."""
        base_load = PowerSystemLoad.example()
        return PhaseLoadEquipment(
            name=base_load.name,
            z_real=base_load.z_real,
            z_imag=base_load.z_imag,
            i_real=base_load.i_real,
            i_imag=base_load.i_imag,
            p_real=base_load.p_real,
            p_imag=base_load.p_imag,
        )
