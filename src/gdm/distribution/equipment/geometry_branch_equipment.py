"""This module contains geometry branch equipment."""

from typing import Annotated

from pydantic import Field, model_validator
from infrasys import Component
import numpy.typing as npt
import numpy as np

from gdm.distribution.equipment.matrix_impedance_branch_equipment import (
    MatrixImpedanceBranchEquipment,
)
from gdm.quantities import Distance, ResistancePULength, ReactancePULength, CapacitancePULength
from gdm.distribution.equipment.concentric_cable_equipment import ConcentricCableEquipment
from gdm.distribution.equipment.bare_conductor_equipment import BareConductorEquipment
from gdm.distribution.enums import LineType, WireInsulationType
from gdm.constants import PINT_SCHEMA


class GeometryBranchEquipment(Component):
    """Data model for geometry branch info."""

    conductors: Annotated[
        list[BareConductorEquipment] | list[ConcentricCableEquipment],
        Field(..., description="List of overhead wires or cables."),
    ]
    horizontal_positions: Annotated[
        Distance,
        PINT_SCHEMA,
        Field(..., description="Horizontal position of the conductor."),
    ]
    vertical_positions: Annotated[
        Distance,
        PINT_SCHEMA,
        Field(
            ...,
            description="""Vertical position of the conductor.""",
        ),
    ]
    insulation: Annotated[
        WireInsulationType,
        PINT_SCHEMA,
        Field(WireInsulationType.AIR, description="Wire insulation type"),
    ]

    @staticmethod
    def _pairwise_distances(A, B):
        return np.linalg.norm(A[:, np.newaxis, :] - B[np.newaxis, :, :], axis=2)

    @staticmethod
    def _kron_reduction(z: Component, num_neutral: int):
        n_phases = len(z) - num_neutral
        z_aa = z[:n_phases, :n_phases]
        z_an = z[:n_phases, n_phases:]
        z_na = z[n_phases:, :n_phases]
        z_nn = z[n_phases:, n_phases:]

        z_reduced = np.squeeze(z_aa - z_an @ np.linalg.inv(z_nn) @ z_na)

        if np.prod(z_reduced.shape) == 1:
            return np.array([[z_reduced]])
        else:
            return z_reduced

    def _calculate_impedance_matrix(
        self,
        dist_matrix: npt.NDArray,
        resistance_arr: list[float] | npt.NDArray,
        num_neutral: int,
        freq: float = 60.0,
        resistivity: float = 100.0,
    ):
        log_term = np.log(1 / dist_matrix) + 7.6786 + 0.5 * np.log(resistivity / freq)
        z = freq * 0.00158836 + 1j * freq * 0.00202237 * log_term
        z[np.diag_indices(len(resistance_arr))] += resistance_arr
        if num_neutral:
            return self._kron_reduction(z, num_neutral)
        else:
            return z

    def _calculate_capacitance_matrix(
        self,
        coords: list[tuple[float, float]],
        dist_matrix: npt.NDArray,
        num_neutral,
    ):
        permittivity = 0.01424 * self.insulation.value
        reflections = coords * np.array([1, -1])
        s = self._pairwise_distances(coords, reflections)
        p = 1 / (2 * np.pi * permittivity) * np.log(s / dist_matrix)
        return np.linalg.inv(self._kron_reduction(p, num_neutral))

    def _get_branch_info(self):
        coordinates = np.array(
            [
                (float(x), float(y))
                for x, y in zip(
                    self.horizontal_positions.to("foot").magnitude,
                    self.vertical_positions.to("foot").magnitude,
                )
            ]
        )
        gmrs = [g.conductor_gmr.to("foot").magnitude for g in self.conductors]
        resistance = [g.ac_resistance.to("ohm/mile").magnitude for g in self.conductors]
        ampacity = sum([g.ampacity for g in self.conductors]) / len(self.conductors)
        radii = [g.conductor_diameter.to("feet").magnitude / 2 for g in self.conductors]
        return coordinates, gmrs, resistance, ampacity, radii

    @staticmethod
    def _get_model_attr(model: Component, attr: str, units: str | None = None):
        if hasattr(model, attr):
            result = getattr(model, attr)
            if hasattr(result, "to") and units:
                return result.to(units).magnitude
            else:
                return result

    def _concentric_cable_config(self, freq: float = 60.0, resistivity: float = 100):
        ampacity = sum([g.ampacity for g in self.conductors]) / len(self.conductors)
        coords = np.array(
            [
                (float(x), float(y))
                for x, y in zip(
                    self.horizontal_positions.to("foot").magnitude,
                    self.vertical_positions.to("foot").magnitude,
                )
            ]
        )
        coords = np.tile(coords, (2, 1))
        n_cond = len(self.conductors)
        n_neut = n_cond
        gmrs = [0] * n_cond * 2
        radii = [0] * n_cond * 2
        ys = []
        for i, c in enumerate(self.conductors):
            gmr_cond = self._get_model_attr(c, "conductor_gmr", "feet")
            grm_strd = self._get_model_attr(c, "strand_gmr", "feet")
            k = self._get_model_attr(c, "num_neutral_strands")
            rad = (c.cable_diameter - c.strand_diameter).to("feet").magnitude / 2
            rad_b = (c.cable_diameter - c.strand_diameter).to("inch").magnitude / 2
            rad_s = c.strand_diameter.to("inch").magnitude / 2
            rad_c = c.conductor_diameter.to("inch").magnitude / 2
            gmr_cn = (grm_strd * k * rad ** (k - 1)) ** (1 / k)
            r_cn = (c.strand_ac_resistance / k).to("ohm/mile").magnitude
            r_c = c.phase_ac_resistance.to("ohm/mile").magnitude
            ys.append(77.3619 / (np.log(rad_b / rad_c) - (1 / k) * np.log(k * rad_s / rad_b)))
            radii[i + n_cond] = r_cn
            radii[i] = rad_c
            gmrs[i + n_cond] = gmr_cn
            gmrs[i] = gmr_cond

        diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
        dist_matrix = np.linalg.norm(diff, axis=2)
        np.fill_diagonal(dist_matrix, gmrs)
        dist_matrix[dist_matrix == 0] = rad
        diag_real_values = np.array([r_c] * n_cond + [r_cn] * n_neut)

        z_reduced = self._calculate_impedance_matrix(
            dist_matrix, diag_real_values, n_neut, freq, resistivity
        )
        np.fill_diagonal(dist_matrix, radii)
        c_reduced = self._calculate_capacitance_matrix(coords, dist_matrix, n_neut)
        np.fill_diagonal(c_reduced, ys)

        return MatrixImpedanceBranchEquipment(
            r_matrix=ResistancePULength(np.real(z_reduced), "ohm/mile"),
            x_matrix=ReactancePULength(np.imag(z_reduced), "ohm/mile"),
            c_matrix=CapacitancePULength(c_reduced, "microfarad/mile"),
            ampacity=ampacity.to("ampere").magnitude,
            construction=LineType.OVERHEAD
            if np.mean(self.vertical_positions) > 0
            else LineType.UNDERGROUND,
            name=self.name,
            uuid=self.uuid,
        )

    def _conductor_config(
        self, num_neutral: int, freq: float = 60.0, resistivity: float = 100
    ) -> MatrixImpedanceBranchEquipment:
        coords, gmrs, resistance, ampacity, radii = self._get_branch_info()

        diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
        dist_matrix = np.linalg.norm(diff, axis=2)
        np.fill_diagonal(dist_matrix, gmrs)

        z_reduced = self._calculate_impedance_matrix(
            dist_matrix, resistance, num_neutral, freq, resistivity
        )
        np.fill_diagonal(dist_matrix, radii)
        c_reduced = self._calculate_capacitance_matrix(coords, dist_matrix, num_neutral)
        return MatrixImpedanceBranchEquipment(
            r_matrix=ResistancePULength(np.real(z_reduced), "ohm/mile"),
            x_matrix=ReactancePULength(np.imag(z_reduced), "ohm/mile"),
            c_matrix=CapacitancePULength(c_reduced, "microfarad/mile"),
            ampacity=ampacity.to("ampere").magnitude,
            construction=LineType.OVERHEAD
            if np.mean(self.vertical_positions) > 0
            else LineType.UNDERGROUND,
            name=self.name,
            uuid=self.uuid,
        )

    def to_matrix_representation(
        self, num_neutral: int, freq: float = 60.0, resistivity: float = 100
    ) -> MatrixImpedanceBranchEquipment:
        """Convert geometry branch equipment to matrix representation."""
        if num_neutral >= len(self.conductors):
            msg = f"Number of neutrals ({num_neutral}) should be less than the total number of conductors ({len(self.conductors)})"
            raise ValueError(msg)

        if isinstance(self.conductors[0], BareConductorEquipment):
            return self._conductor_config(num_neutral)
        elif isinstance(self.conductors[0], ConcentricCableEquipment):
            return self._concentric_cable_config()
        else:
            raise NotImplementedError(
                f"No implementation for conductor type {self.conductors[0].__class__.__name__}"
            )

    @model_validator(mode="after")
    def validate_fields(self) -> "GeometryBranchEquipment":
        """Custom validator for geometry branch model fields."""
        if not self.conductors:
            msg = f"Number of wires must be at least 1 {self.conductors=}"
            raise ValueError(msg)

        if len(self.horizontal_positions) != len(self.conductors):
            msg = f"Number of horizontal_positions ({len(self.horizontal_positions)}) and conductors ({len(self.conductors)}) must be equal in length."
            raise ValueError(msg)

        if len(self.vertical_positions) != len(self.conductors):
            msg = f"Number of vertical_positions ({len(self.vertical_positions)}) and conductors ({len(self.conductors)}) must be equal in length."
            raise ValueError(msg)

        return self

    @classmethod
    def example(cls) -> "GeometryBranchEquipment":
        """Example for geometry branch equipment."""
        return GeometryBranchEquipment(
            name="geometry-branch-1",
            conductors=[BareConductorEquipment.example()] * 3,
            horizontal_positions=Distance([5.6, 6.0, 6.4], "m"),
            vertical_positions=Distance([5.6, 6.0, 6.4], "m"),
        )
