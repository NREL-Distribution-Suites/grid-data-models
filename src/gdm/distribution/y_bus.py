from math import pi

from scipy.sparse import coo_matrix
import numpy as np

from gdm.distribution.components.base.distribution_transformer_base import (
    DistributionTransformerBase,
)
from gdm.distribution.enums import Phase, ConnectionType
from gdm.distribution.equipment import WindingEquipment
from gdm.distribution.components import (
    DistributionVoltageSource,
    MatrixImpedanceBranch,
    MatrixImpedanceSwitch,
    DistributionBus,
    GeometryBranch,
)
from gdm.distribution import DistributionSystem
from gdm.quantities import ApparentPower, Frequency


class YBus:
    def __init__(
        self,
        system: DistributionSystem,
        base_va: ApparentPower = ApparentPower(1e6, "va"),
        freq: Frequency = Frequency(60, "hertz"),
    ) -> None:
        self.system = system
        self.base_va = base_va.to("va")
        self.freq = freq.to("hertz")

    def _build_bus_index(self, in_service_nodes):
        bus_phase_index = {}
        idx = 0
        for bus_name in in_service_nodes:
            bus = self.system.get_component(DistributionBus, bus_name)
            for ph in bus.phases:
                bus_phase_index[(bus_name, ph)] = idx
                idx += 1
        return bus_phase_index

    def _get_line_admittance_matrix(
        self, component: MatrixImpedanceBranch
    ) -> tuple[np.matrix, np.matrix, list[Phase]]:
        """Builds the admittance matrix for the distribution system."""
        model_phases = component.phases

        r_matrix = component.equipment.r_matrix.to("ohm / meter")
        x_matrix = component.equipment.x_matrix.to("ohm / meter")
        c_matrix = component.equipment.c_matrix.to("farad / meter")

        z_pul = r_matrix + 1j * x_matrix
        z_ohms = (z_pul * component.length.to("meter")).magnitude
        c_farads = (c_matrix * component.length.to("meter")).magnitude

        y_series = np.linalg.inv(z_ohms)
        y_shunt = 1j * 2 * pi * self.freq.magnitude * c_farads

        return y_series, y_shunt, model_phases

    @staticmethod
    def _add_line_to_ybus(
        row: list,
        col: list,
        data: list,
        model_phases: list[Phase],
        bus_phase_index: dict[str, Phase],
        y_series: np.ndarray,
        y_shunt: np.ndarray,
        u: int,
        v: int,
    ):
        y_total = y_series + 0.5 * y_shunt
        for i, phi in enumerate(model_phases):
            for j, phj in enumerate(model_phases):
                iu = bus_phase_index[(u, phi)]
                iv = bus_phase_index[(v, phj)]
                # Self
                if y_total[i, j] != 0 + 0j:
                    row.append(iu)
                    col.append(iu)
                    data.append(y_total[i, j])
                    row.append(iv)
                    col.append(iv)
                    data.append(y_total[i, j])
                # Mutual
                if y_series[i, j] != 0 + 0j:
                    row.append(iu)
                    col.append(iv)
                    data.append(-y_series[i, j])
                    row.append(iv)
                    col.append(iu)
                    data.append(-y_series[i, j])

    @staticmethod
    def _xfmr_transform(winding: WindingEquipment, phase_shift_deg=0.0):
        shift = np.exp(1j * np.deg2rad(phase_shift_deg))
        turns_ratio = np.array(winding.tap_positions)
        if winding.connection_type == ConnectionType.STAR:
            T = np.eye(3, dtype=complex) / turns_ratio
        elif winding.connection_type == ConnectionType.DELTA:
            T = np.array([[1, -1, 0], [0, 1, -1], [-1, 0, 1]], dtype=complex) / turns_ratio
            T = np.eye(3, dtype=complex) / turns_ratio
        elif winding.connection_type == ConnectionType.OPEN_DELTA:
            T = np.array([[1, -1, 0], [0, 1, -1]], dtype=complex) / turns_ratio
        elif winding.connection_type == ConnectionType.ZIG_ZAG:
            T = (
                np.array([[0.5, -0.5, 0.0], [0.0, 0.5, -0.5], [-0.5, 0.0, 0.5]], dtype=complex)
                / turns_ratio
            )
        else:
            raise ValueError(f"Unknown transformer connection: {winding.connection_type}")
        return T * shift

    def _add_xfmr_to_ybus(
        self,
        xfmr: DistributionTransformerBase,
        row: list,
        col: list,
        values: list,
        bus_phase_index: dict[str, Phase],
        u: int,
        v: int,
    ):
        phases = xfmr.winding_phases[0]
        z = xfmr.get_sc_impedance()
        if len(phases) == 3:
            transforms = [self._xfmr_transform(wdg) for wdg in xfmr.equipment.windings]
            n_ii = [len(t) for t in transforms]
            z_xfmr = np.zeros((sum(n_ii), sum(n_ii)), dtype=complex)

            np.fill_diagonal(z_xfmr, z.to("ohm").magnitude)
            y_sc = np.linalg.inv(z_xfmr)
            y_pp = y_sc[: n_ii[0], : n_ii[0]]
            y_ps = y_sc[: n_ii[0], n_ii[0] :]
            y_sp = y_sc[n_ii[0] :, : n_ii[0]]
            y_ss = y_sc[n_ii[0] :, n_ii[0] :]

            y11 = transforms[0].conj().T @ y_pp @ transforms[0]
            y12 = transforms[0].conj().T @ y_ps @ transforms[1]
            y21 = transforms[1].conj().T @ y_sp @ transforms[0]
            y22 = transforms[1].conj().T @ y_ss @ transforms[1]

        else:
            n = 2
            z_xfmr = np.zeros((n, n), dtype=complex)
            y11, y21, y12, y22 = [z_xfmr] * n * 2

        for i, phi_i in enumerate(phases):
            for j, phi_j in enumerate(phases):
                iu = bus_phase_index[(v, phi_i)]
                iv = bus_phase_index[(u, phi_j)]

                # if y11[i, j] != 0 + 0j:
                #     row.append(iu); col.append(iu); values.append(y11[i, j])
                # if y22[i, j] != 0 + 0j:
                #     row.append(iv); col.append(iv); values.append(y22[i, j])
                if i == j:
                    if y12[i, j] != 0 + 0j:
                        row.append(iu)
                        col.append(iv)
                        values.append(y12[i, j])
                    if y21[i, j] != 0 + 0j:
                        row.append(iv)
                        col.append(iu)
                        values.append(y21[i, j])

    def _add_source_to_ybus(
        self,
        row: list,
        col: list,
        values: list,
        bus_phase_index: dict[str, Phase],
    ):
        v_sources = self.system.get_components(DistributionVoltageSource)
        for v_source in v_sources:
            u = v_source.bus.name
            z_src = v_source.get_impedance_matrix()
            y_src = np.linalg.inv(z_src)
            for i, phi_i in enumerate(v_source.phases):
                iu = bus_phase_index[(u, phi_i)]
                row.append(iu)
                col.append(iu)
                values.append(y_src[i, i])
                for j, phi_j in enumerate(v_source.phases):
                    if i != j:
                        iv = bus_phase_index[(u, phi_j)]
                        if y_src[i, j] != 0 + 0j:
                            row.append(iv)
                            col.append(iu)
                            values.append(-y_src[i, j])

    def build_ybus_sparse(self) -> tuple[coo_matrix, dict[str, Phase]]:
        graph = self.system.get_undirected_graph()
        in_service_edges = [
            (u, v, attr) for u, v, attr in graph.edges(data=True) if attr.get("in_service")
        ]
        in_service_nodes = sorted(list({e for edge in in_service_edges for e in edge[:-1]}))

        bus_phase_index = self._build_bus_index(in_service_nodes)
        row, col, values = [], [], []

        self._add_source_to_ybus(row, col, values, bus_phase_index)

        for u, v, data in in_service_edges:
            model_name = data["name"]
            model_type = data["type"]
            component = self.system.get_component(model_type, model_name)

            if isinstance(component, (MatrixImpedanceBranch, MatrixImpedanceSwitch)):
                y_series, y_shunt, model_phases = self._get_line_admittance_matrix(component)
                self._add_line_to_ybus(
                    row, col, values, model_phases, bus_phase_index, y_series, y_shunt, u, v
                )
            elif isinstance(component, GeometryBranch):
                y_series, y_shunt, model_phases = self._get_line_admittance_matrix(
                    component.to_matrix_representation()
                )
                self._add_line_to_ybus(
                    row, col, values, model_phases, bus_phase_index, y_series, y_shunt, u, v
                )
            elif isinstance(component, DistributionTransformerBase):
                xfmrs_u = self.system.get_bus_connected_components(u, DistributionTransformerBase)
                xfmrs_v = self.system.get_bus_connected_components(v, DistributionTransformerBase)
                xfmrs_all = xfmrs_u + xfmrs_v
                xfmr_names = set(xu.name for xu in xfmrs_u).intersection(xv.name for xv in xfmrs_v)
                edge_xfmrs: dict[str, DistributionTransformerBase] = {
                    xfmr.name: xfmr for xfmr in xfmrs_all if xfmr.name in xfmr_names
                }
                for xfmr in edge_xfmrs.values():
                    self._add_xfmr_to_ybus(xfmr, row, col, values, bus_phase_index, u, v)
            else:
                raise TypeError(f"Unsupported component type: {type(component)}")

        n = len(bus_phase_index)
        return coo_matrix((values, (row, col)), shape=(n, n)), bus_phase_index
