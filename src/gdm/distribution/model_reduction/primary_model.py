from pathlib import Path

from loguru import logger
import networkx as nx

from gdm.distribution.components.base.distribution_transformer_base import (
    DistributionTransformerBase,
)
from gdm.distribution.equipment.capacitor_equipment import (
    CapacitorEquipment,
    PhaseCapacitorEquipment,
)
from gdm.distribution.components.base.distribution_branch_base import DistributionBranchBase
from gdm.distribution.components.distribution_solar import DistributionSolar, SolarEquipment
from gdm.distribution.equipment.load_equipment import LoadEquipment, PhaseLoadEquipment
from gdm.distribution.components.distribution_vsource import DistributionVoltageSource
from gdm.distribution.components.distribution_capacitor import DistributionCapacitor
from gdm.distribution.components.distribution_load import DistributionLoad
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.distribution_graph import build_graph_from_system
from gdm.distribution.distribution_system import DistributionSystem
from gdm.distribution.distribution_enum import ConnectionType
from infrasys.exceptions import ISNotStored


class PrimaryModel:
    def __init__(self, distribution_system: DistributionSystem):
        self._distribution_system = distribution_system
        self._graph = build_graph_from_system(distribution_system)
        self._all_buses = set(self._graph.nodes)
        self._source_buses = self.get_source_bus(self._distribution_system)
        assert len(set(self._source_buses)) == 1, "Source bus should be singular"
        self._tree = nx.dfs_tree(self._graph, source=self._source_buses[0])
        for u, v in self._tree.edges():
            attrs = self._graph.edges[u, v]
            self._tree.add_edge(u, v, **attrs)

    @classmethod
    def from_json(cls, json_path: Path | str):
        json_path = Path(json_path)
        return cls(DistributionSystem.from_json(json_path))

    def get_source_bus(self, distribution_system: DistributionSystem):
        voltage_sources = distribution_system.get_components(DistributionVoltageSource)
        buses = [v_source.bus.name for v_source in voltage_sources]
        return buses

    def build(self) -> DistributionSystem:
        all_subtree_buses = []
        components = {}

        primary_buses = [
            bus.name
            for bus in self._distribution_system.get_components(
                DistributionBus,
                filter_func=lambda x: x.nominal_voltage.to("kilovolt").magnitude > 1.0,
            )
        ]
        logger.info(f"Number of primary buses identified: {len(primary_buses)}")

        primary_network = self._graph.subgraph(primary_buses)
        logger.info("Building primary skeleton")
        primary_system: DistributionSystem = self.build_primary_model(primary_network)
        logger.info("Primary skeleton build complete")

        distribution_xfmr_hv_buses = set(
            [
                xfmr.buses[0].name
                for xfmr in self._distribution_system.get_components(
                    DistributionTransformerBase,
                    filter_func=lambda x: x.equipment.windings[0]
                    .rated_power.to("kilova")
                    .magnitude
                    < 5000,
                )
            ]
        )
        logger.info(
            f"Number of HV distribution transformer buses identified: {len(distribution_xfmr_hv_buses)}"
        )

        for i, primary_bus in enumerate(distribution_xfmr_hv_buses):
            logger.info(
                f"Primary lump load complete: {i / len(distribution_xfmr_hv_buses) * 100.0}"
            )

            subgraph = self._graph.subgraph(nx.descendants(self._tree, primary_bus))
            all_subtree_buses.extend(list(subgraph.nodes))

            ld_kw, ld_kvar, gen_kw, cap_kvar = self._lump_graph_load_and_generation(subgraph)
            components[primary_bus] = {
                "ld_kw": ld_kw,
                "ld_kvar": ld_kvar,
                "gen_kw": gen_kw,
                "cap_kvar": cap_kvar,
            }

        primary_system = self.add_lumped_components_to_primary(primary_system, components)
        return primary_system

    def add_lumped_load(
        self,
        bus_name: str,
        bus: DistributionBus,
        primary: DistributionSystem,
        lumped_components: dict[str, dict],
    ):
        if lumped_components[bus_name]["ld_kw"] + lumped_components[bus_name]["ld_kvar"] != 0:
            load = DistributionLoad(
                name=f"lump_load_{bus_name}",
                bus=bus,
                phases=bus.phases,
                equipment=LoadEquipment(
                    name=f"lump_load_{bus_name}_equipment",
                    phase_loads=[
                        PhaseLoadEquipment(
                            name=f"lump_load_{bus_name}_{phase.value}",
                            real_power=lumped_components[bus_name]["ld_kw"] / len(bus.phases),
                            reactive_power=lumped_components[bus_name]["ld_kvar"]
                            / len(bus.phases),
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
            primary.add_component(load)

    def add_lumped_generator(
        self,
        bus_name: str,
        bus: DistributionBus,
        primary: DistributionSystem,
        lumped_components: dict[str, dict],
    ):
        if lumped_components[bus_name]["gen_kw"] != 0:
            generator = DistributionSolar(
                name=f"lump_generator_{bus_name}",
                bus=bus,
                phases=bus.phases,
                equipment=SolarEquipment(
                    name=f"lump_generator_{bus_name}_equipment",
                    rated_capacity=lumped_components[bus_name]["gen_kw"],
                    solar_power=lumped_components[bus_name]["gen_kw"],
                    resistance=1e-6,
                    reactance=1e-6,
                    cutin_percent=10.0,
                    cutout_percent=10.0,
                ),
            )
            primary.add_component(generator)

    def add_lumped_capacitor(
        self,
        bus_name: str,
        bus: DistributionBus,
        primary: DistributionSystem,
        lumped_components: dict[str, dict],
    ):
        if lumped_components[bus_name]["cap_kvar"] != 0:
            capacitor = DistributionCapacitor(
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
                            rated_capacity=lumped_components[bus_name]["cap_kvar"]
                            / len(bus.phases),
                            num_banks=1,
                            num_banks_on=1,
                        )
                        for phase in bus.phases
                    ],
                ),
            )
            primary.add_component(capacitor)

    def add_lumped_components_to_primary(
        self, primary: DistributionSystem, lumped_components: dict[str, dict]
    ) -> DistributionSystem:
        for bus_name in lumped_components:
            print(lumped_components[bus_name])
            try:
                bus: DistributionBus = primary.get_component(DistributionBus, bus_name)
                self.add_lumped_load(bus_name, bus, primary, lumped_components)
                self.add_lumped_generator(bus_name, bus, primary, lumped_components)
                self.add_lumped_capacitor(bus_name, bus, primary, lumped_components)
            except Exception:
                # TODO: @aadil to fix this logic before merge
                logger.warning("Error adding component")

        return primary

    def build_primary_model(self, primary_network: nx.Graph):
        primary_buses = list(primary_network.nodes)
        primary_system = DistributionSystem(
            name="primary",
            auto_add_composed_components=True,
        )
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
                        primary_system.get_component(type(model), model.name)
                        logger.warning(
                            f"{model.__class__.__name__}.{model.name} already exists in the primary network"
                        )
                    except ISNotStored:
                        logger.info(
                            f"{model.__class__.__name__}.{model.name} added to the primary network"
                        )
                        primary_system.add_component(model)
            else:
                primary_system.add_component(
                    self._distribution_system.get_component(DistributionBus, bus)
                )

        return primary_system

    def _lump_graph_load_and_generation(self, subgraph: nx.Graph):
        bus_names = list(subgraph.nodes)
        loads: list[DistributionLoad] = []
        generators: list[DistributionSolar] = []
        capacitors: list[DistributionCapacitor] = []

        for bus in bus_names:
            loads.extend(
                self._distribution_system.get_bus_connected_components(bus, DistributionLoad)
            )
            generators.extend(
                self._distribution_system.get_bus_connected_components(bus, DistributionSolar)
            )
            capacitors.extend(
                self._distribution_system.get_bus_connected_components(bus, DistributionCapacitor)
            )

        total_load_kw = 0
        total_load_kvar = 0
        for load in loads:
            total_load_kw += sum(
                [phs_load.real_power.magnitude for phs_load in load.equipment.phase_loads]
            )
            total_load_kvar += sum(
                [phs_load.reactive_power.magnitude for phs_load in load.equipment.phase_loads]
            )

        total_generator_capacity_kw = 0
        for generator in generators:
            total_generator_capacity_kw += generator.equipment.rated_capacity.magnitude

        total_capacitor_capacity_kvar = 0
        for capacitor in capacitors:
            total_capacitor_capacity_kvar += sum(
                [
                    capacitor.rated_capacity.magnitude
                    for capacitor in capacitor.equipment.phase_capacitors
                ]
            )

        return (
            total_load_kw,
            total_load_kvar,
            total_generator_capacity_kw,
            total_capacitor_capacity_kvar,
        )
