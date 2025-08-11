"""This module contains interface for distribution substation."""

from typing import Annotated
from math import pi

from pydantic import Field
import numpy as np

from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.enums import Phase
from gdm.distribution.components.base.distribution_component_base import (
    InServiceDistributionComponentBase,
)
from gdm.distribution.components.distribution_feeder import DistributionFeeder
from gdm.distribution.components.distribution_substation import DistributionSubstation
from gdm.distribution.equipment.voltagesource_equipment import VoltageSourceEquipment


class DistributionVoltageSource(InServiceDistributionComponentBase):
    """Data model for distribution substation."""

    bus: Annotated[
        DistributionBus,
        Field(
            ...,
            description="Distribution bus to which this voltage source is connected to.",
        ),
    ]
    phases: Annotated[list[Phase], Field(..., description="Phase to which this is connected to.")]
    equipment: Annotated[VoltageSourceEquipment, Field(..., description="Voltage source model.")]

    def get_impedance_matrix(self):
        """Returns the impedance matrix of the voltage source."""
        z0 = [src.r0 + 1j * src.x0 for src in self.equipment.sources][0].to("ohm").magnitude
        z1 = [src.r1 + 1j * src.x1 for src in self.equipment.sources][0].to("ohm").magnitude
        z2 = z1

        a = np.exp(1j * 2.0 * pi / 3.0)
        zseq = np.diag([z0, z1, z2])
        transform = np.array([[1.0, 1.0, 1.0], [1.0, a**2, a], [1.0, a, a**2]], dtype=complex)
        transform_inv = np.linalg.inv(transform)
        z_abc = transform @ zseq @ transform_inv
        return z_abc

    @classmethod
    def example(cls) -> "DistributionVoltageSource":
        """Example for distribution voltage source."""
        return DistributionVoltageSource(
            name="DistributionVoltageSource1",
            bus=DistributionBus.example(),
            phases=[Phase.A, Phase.B, Phase.C],
            substation=DistributionSubstation.example(),
            feeder=DistributionFeeder.example(),
            equipment=VoltageSourceEquipment.example(),
        )
