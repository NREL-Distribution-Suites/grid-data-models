from pathlib import Path

from abc import ABC, abstractmethod

from gdm.distribution.distribution_graph import build_graph_from_system
from infrasys.exceptions import ISNotStored
from gdm import (
    DistributionTransformerBase,
    DistributionVoltageSource,
    PhaseCapacitorEquipment,
    DistributionBranchBase,
    DistributionCapacitor,
    DistributionSystem,
    PhaseLoadEquipment,
    CapacitorEquipment,
    DistributionSolar,
    DistributionLoad,
    DistributionBus,
    SolarEquipment,
    ConnectionType,
    LoadEquipment,
    Phase,
)
from gdm.quantities import (
    PositiveReactivePower,
    PositiveActivePower,
    ReactivePower,
    ActivePower,
)
from pydantic import BaseModel
from loguru import logger
import networkx as nx


class LumpedComponent(BaseModel):
    load_kw: dict[Phase, float] = {Phase.A: 0, Phase.B: 0, Phase.C: 0, Phase.S1: 0, Phase.S2: 0}
    load_kvar: dict[Phase, float] = {Phase.A: 0, Phase.B: 0, Phase.C: 0, Phase.S1: 0, Phase.S2: 0}
    capacitor_kvar: dict[Phase, float] = {
        Phase.A: 0,
        Phase.B: 0,
        Phase.C: 0,
        Phase.S1: 0,
        Phase.S2: 0,
    }
    solar_kw: float = 0


class AbstractReducer(ABC):
    def __init__(self, distribution_system: DistributionSystem) -> None:
        self._distribution_system = distribution_system
        self._graph = build_graph_from_system(distribution_system)
        self._all_buses = set(self._graph.nodes)
        self._source_buses = self._get_source_bus(self._distribution_system)
        assert len(set(self._source_buses)) == 1, "Source bus should be singular"
        self._tree = nx.dfs_tree(self._graph, source=self._source_buses[0])
        for u, v in self._tree.edges():
            attrs = self._graph.edges[u, v]
            self._tree.add_edge(u, v, **attrs)

    @classmethod
    def from_json(cls, json_path: Path | str):
        json_path = Path(json_path)
        return cls(DistributionSystem.from_json(json_path))

    def _get_source_bus(self, distribution_system: DistributionSystem):
        voltage_sources = distribution_system.get_components(DistributionVoltageSource)
        buses = [v_source.bus.name for v_source in voltage_sources]
        return buses

    @abstractmethod
    def build(self) -> DistributionSystem:
        return

    def _add_lumped_load(
        self,
        bus_name: str,
        bus: DistributionBus,
        lumped_load: LumpedComponent,
    ) -> DistributionLoad:
        nphases = len(bus.phases)
        split_phases = [Phase.S1, Phase.S2]
        split_phase_load_kw = sum([lumped_load.load_kw[phs] for phs in split_phases]) / nphases
        split_phase_load_kvar = sum([lumped_load.load_kvar[phs] for phs in split_phases]) / nphases
        return DistributionLoad(
            name=f"lump_load_{bus_name}",
            bus=bus,
            phases=bus.phases,
            equipment=LoadEquipment(
                name=f"lump_load_{bus_name}_equipment",
                phase_loads=[
                    PhaseLoadEquipment(
                        name=f"lump_load_{bus_name}_{phase.value}",
                        real_power=ActivePower(
                            lumped_load.load_kw[phase] + split_phase_load_kw, "kilowatt"
                        ),
                        reactive_power=ReactivePower(
                            lumped_load.load_kvar[phase] + split_phase_load_kvar, "kilovar"
                        ),
                        z_real=0.0,
                        z_imag=0.0,
                        i_real=0.0,
                        i_imag=0.0,
                        p_real=1.0,
                        p_imag=1.0,
                    )
                    for phase in bus.phases
                ],
                connection_type=ConnectionType.STAR,
            ),
        )

    def _add_lumped_generator(
        self,
        bus_name: str,
        bus: DistributionBus,
        lumped_generator: LumpedComponent,
    ) -> DistributionSolar:
        return DistributionSolar(
            name=f"lump_generator_{bus_name}",
            bus=bus,
            phases=bus.phases,
            equipment=SolarEquipment(
                name=f"lump_generator_{bus_name}_equipment",
                rated_capacity=PositiveActivePower(lumped_generator.solar_kw, "kilowatt"),
                solar_power=PositiveActivePower(lumped_generator.solar_kw, "kilowatt"),
                resistance=1e-6,
                reactance=1e-6,
                cutin_percent=10.0,
                cutout_percent=10.0,
            ),
        )

    def _add_lumped_capacitor(
        self,
        bus_name: str,
        bus: DistributionBus,
        lumped_capacitor: LumpedComponent,
    ) -> DistributionCapacitor:
        return DistributionCapacitor(
            name=f"lump_capacitor_{bus_name}",
            bus=bus,
            phases=bus.phases,
            equipment=CapacitorEquipment(
                name=f"lump_capacitor_{bus_name}_equipment",
                connection_type=ConnectionType.STAR,
                phase_capacitors=[
                    PhaseCapacitorEquipment(
                        name=f"lump_capacitor_{bus_name}_equipment_{phase.value}",
                        resistance=1e-6,
                        reactance=1e-6,
                        rated_capacity=PositiveReactivePower(
                            lumped_capacitor.capacitor_kvar[phase], "kilovar"
                        ),
                        num_banks=1,
                        num_banks_on=1,
                    )
                    for phase in bus.phases
                ],
            ),
        )

    def _add_lumped_components_to_primary(
        self, reduced_system: DistributionSystem, lumped_components: dict[str, LumpedComponent]
    ) -> DistributionSystem:
        added_total_load_kw = 0
        added_total_load_kvar = 0
        for bus_name in lumped_components:
            bus: DistributionBus = reduced_system.get_component(DistributionBus, bus_name)
            lumped_model_data = lumped_components[bus_name]

            comp_total_load_kw = sum(lumped_model_data.load_kw.values())
            comp_total_load_kvar = sum(lumped_model_data.load_kw.values())

            if not (comp_total_load_kw == 0 and comp_total_load_kvar == 0):
                reduced_system.add_component(
                    self._add_lumped_load(bus_name, bus, lumped_model_data)
                )
                added_total_load_kw += comp_total_load_kw
                added_total_load_kvar += comp_total_load_kvar
            if lumped_model_data.solar_kw != 0:
                reduced_system.add_component(
                    self._add_lumped_generator(bus_name, bus, lumped_model_data)
                )
            if sum(lumped_model_data.capacitor_kvar.values()) != 0:
                reduced_system.add_component(
                    self._add_lumped_capacitor(bus_name, bus, lumped_model_data)
                )

        print(f"{added_total_load_kw=}")
        print(f"{added_total_load_kvar=}")
        return reduced_system

    def _build_lumped_components(self, subgraph: nx.Graph) -> LumpedComponent:
        bus_names = list(subgraph.nodes)
        loads: list[DistributionLoad] = []
        solars: list[DistributionSolar] = []
        capacitors: list[DistributionCapacitor] = []

        lumped_model = LumpedComponent()

        for bus in bus_names:
            loads.extend(
                self._distribution_system.get_bus_connected_components(bus, DistributionLoad)
            )
            solars.extend(
                self._distribution_system.get_bus_connected_components(bus, DistributionSolar)
            )
            capacitors.extend(
                self._distribution_system.get_bus_connected_components(bus, DistributionCapacitor)
            )

        for load in loads:
            for phase, phs_load in zip(load.phases, load.equipment.phase_loads):
                lumped_model.load_kw[phase] += phs_load.real_power.to("kilowatt").magnitude
                lumped_model.load_kvar[phase] += phs_load.reactive_power.to("kilovar").magnitude

        for solar in solars:
            lumped_model.solar_kw += solar.equipment.rated_capacity.to("kilovar").magnitude

        for capacitor in capacitors:
            for phase, phs_cap in zip(capacitor.phases, capacitor.equipment.phase_capacitors):
                lumped_model.capacitor_kvar[phase] += phs_cap.rated_capacity.to("kilova").magnitude

        return lumped_model

    def _build_reduced_network_skeleton(
        self, reduced_system: DistributionSystem, primary_network: nx.Graph
    ) -> DistributionSystem:
        primary_buses = list(primary_network.nodes)
        for bus in primary_buses:
            models = []
            for model_type in [
                DistributionLoad,
                DistributionSolar,
                DistributionCapacitor,
                DistributionBranchBase,
                DistributionVoltageSource,
                DistributionTransformerBase,
            ]:
                queried_models = self._distribution_system.get_bus_connected_components(
                    bus, model_type
                )
                if model_type not in [DistributionBranchBase, DistributionTransformerBase]:
                    models.extend(queried_models)
                else:
                    for queried_model in queried_models:
                        edge_buses = set([b.name for b in queried_model.buses])
                        if edge_buses.issubset(primary_buses):
                            models.append(queried_model)
            if models:
                for model in models:
                    try:
                        reduced_system.get_component(type(model), model.name)
                        logger.warning(
                            f"{model.__class__.__name__}.{model.name} already exists in the primary network"
                        )
                    except ISNotStored:
                        logger.info(
                            f"{model.__class__.__name__}.{model.name} added to the primary network"
                        )
                        reduced_system.add_component(model)
            else:
                reduced_system.add_component(
                    self._distribution_system.get_component(DistributionBus, bus)
                )

        return reduced_system
