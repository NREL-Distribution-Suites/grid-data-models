"""This module contains distribution system."""

from typing import Annotated, Type
import importlib.metadata
from pathlib import Path

from infrasys import Component, System
from pydantic import BaseModel, Field
import plotly.graph_objects as go
import plotly.colors as pc
from loguru import logger
import geopandas as gpd
import networkx as nx
import shapely
import numpy as np


from gdm.distribution.components.base.distribution_branch_base import (
    DistributionBranchBase,
)
from gdm.distribution.components.base.distribution_transformer_base import (
    DistributionTransformerBase,
)
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.components.distribution_transformer import (
    DistributionTransformer,
)
from gdm.distribution.components.distribution_vsource import (
    DistributionVoltageSource,
)
from gdm.distribution.distribution_enum import Phase
from gdm.distribution.system_to_gdf import Converter
from gdm.exceptions import (
    MultipleOrEmptyVsourceFound,
)
from gdm.distribution.distribution_enum import ColorNodeBy, ColorLineBy


class UserAttributes(BaseModel):
    """Interface for single time series data user attributes."""

    profile_name: Annotated[
        str, Field(..., description="Name of the profile to be used in original powerflow model.")
    ]
    profile_type: Annotated[
        str, Field(..., description="Type of profile could be PMult, QMult etc.")
    ]
    use_actual: Annotated[
        bool,
        Field(..., description="Boolean flag indicating whether these values are actual or not."),
    ]


class DistributionSystem(System):
    """Class interface for distribution system."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_format_version = importlib.metadata.version("grid-data-models")

    def get_bus_connected_components(
        self, bus_name: str, component_type: Component
    ) -> list[Component] | None:
        """Returns list of components connected to this bus."""

        if "bus" in component_type.model_fields:
            return list(
                filter(
                    lambda x: x.bus.name == bus_name,
                    self.get_components(component_type),
                )
            )
        elif "buses" in component_type.model_fields:
            return list(
                filter(
                    lambda x: bus_name in [bus.name for bus in x.buses],
                    self.get_components(component_type),
                )
            )

    def get_model_types_with_field_type(
        self, field_type: Type[Component]
    ) -> list[Type[Component]]:
        return [
            model_type
            for model_type in self.get_component_types()
            if any(
                [field.annotation == field_type for _, field in model_type.model_fields.items()]
            )
        ]

    def get_source_bus(self) -> DistributionBus:
        voltage_sources = self.get_components(DistributionVoltageSource)
        buses = [v_source.bus for v_source in voltage_sources]
        if len(buses) != 1:
            msg = f"Multiple or no vsource found for this system {buses}."
            raise MultipleOrEmptyVsourceFound(msg)
        return buses[0]

    def get_undirected_graph(self) -> nx.Graph:
        graph = nx.Graph()
        node: DistributionBus
        for node in self.get_components(DistributionBus):
            graph.add_node(node.name)

        edges: list[DistributionBranchBase | DistributionTransformerBase] = list(
            self.get_components(DistributionBranchBase)
        ) + list(self.get_components(DistributionTransformerBase))

        for edge in edges:
            graph.add_edge(
                edge.buses[0].name,
                edge.buses[1].name,
                **{"name": edge.name, "type": edge.__class__},
            )
        return graph

    def get_subsystem(
        self, bus_names: list[str], name: str, keep_timeseries: bool = False
    ) -> "DistributionSystem":
        """Method to get subsystem from list of buses.

        Parameters
        ----------
        bus_names: list[str]
            List of bus names
        name: str
            Name of the subsystem.
        keep_timeseries: bool
            Set this flag to retain timeseries data associated with the component.

        Returns
        -------
        DistributionSystem
        """
        tree = self.get_directed_graph()
        subtree = tree.subgraph(bus_names)
        subtree_system = DistributionSystem(auto_add_composed_components=True, name=name)
        for u, v, _ in subtree.edges(data=True):
            parent_components = self.list_parent_components(
                self.get_component(DistributionBus, u)
            ) + self.list_parent_components(self.get_component(DistributionBus, v))
            for component in parent_components:
                if isinstance(
                    component,
                    (DistributionBranchBase, DistributionTransformerBase),
                ):
                    nodes = {bus.name for bus in component.buses}
                    if not nodes.issubset(set(bus_names)):
                        continue
                if not subtree_system.has_component(component):
                    subtree_system.add_component(component)
        if keep_timeseries:
            for comp in subtree_system.get_components(
                Component, filter_func=lambda x: self.has_time_series(x)
            ):
                ts_metadata = self.list_time_series_metadata(comp)
                for metadata in ts_metadata:
                    ts_data = self.get_time_series(comp, metadata.variable_name)
                    subtree_system.add_time_series(ts_data, comp, **metadata.user_attributes)

        return subtree_system

    def get_directed_graph(self) -> nx.DiGraph:
        ugraph = self.get_undirected_graph()
        return nx.dfs_tree(ugraph, source=self.get_source_bus().name)

    def get_split_phase_mapping(self) -> dict[str, set[Phase]]:
        split_phase_map = {}
        original_tree = self.get_directed_graph()
        split_phase_trs: list[DistributionTransformer] = list(
            self.get_components(
                DistributionTransformer,
                filter_func=lambda x: x.equipment.is_center_tapped,
            )
        )
        for tr in split_phase_trs:
            lv_bus = {
                bus.name for bus in tr.buses if Phase.S1 in bus.phases or Phase.S2 in bus.phases
            }.pop()
            hv_bus = (set([bus.name for bus in tr.buses]) - set([lv_bus])).pop()
            lv_system = self.get_subsystem(
                list(nx.descendants(original_tree, lv_bus)) + [lv_bus], name=""
            )
            bus_model_types = self.get_model_types_with_field_type(DistributionBus)
            for model_type in bus_model_types:
                for asset in lv_system.get_components(model_type):
                    split_phase_map[asset.name] = set(
                        self.get_component(DistributionBus, hv_bus).phases
                    )
        return split_phase_map

    def to_gdf(self, export_path: Path | None = None) -> gpd.GeoDataFrame:
        if export_path:
            export_path = Path(export_path)

        converter = Converter(self)
        nodes_gdf, edges_gdf = converter.build_dataframes()
        if export_path and export_path.exists() and export_path.is_dir():
            nodes_gdf.to_csv(export_path / f"{self.name}_nodes_gdf.csv")
            edges_gdf.to_csv(export_path / f"{self.name}_edges_gdf.csv")
        elif export_path and export_path.exists() and not export_path.is_dir():
            raise NotADirectoryError("Provided path is not a directory")
        elif export_path and not export_path.exists():
            raise FileNotFoundError("Provided path does not exist")

        return nodes_gdf, edges_gdf

    def plot(
        self,
        export_path: Path | None = None,
        zoom_level: int = 24,
        show: bool = True,
        color_node_by: ColorNodeBy = ColorNodeBy.PHASE,
        color_line_by: ColorLineBy = ColorLineBy.TYPE,
    ) -> None:
        nodes_gdf, edges_gdf = self.to_gdf()
        center = nodes_gdf.unary_union.centroid
        nodes_gdf["lon"] = nodes_gdf.geometry.y
        nodes_gdf["lat"] = nodes_gdf.geometry.x

        fig = go.Figure()

        self._add_node_traces(fig, nodes_gdf, color_node_by)
        self._add_edge_traces(fig, edges_gdf, color_line_by)

        fig.update_layout(
            title=f"GDM plot for {self.name} distribution system",
            geo=dict(
                center=dict(lat=center.x, lon=center.y),  # Set center
                projection_scale=zoom_level,  # Adjust zoom (lower value = more zoomed-in)
                showland=True,
                landcolor="lightgray",
            ),
        )

        if show:
            fig.show()
        if export_path:
            export_path = Path(export_path)
            if export_path.exists() and export_path.is_dir():
                fig.write_html(export_path / f"{self.name}_plot.html")
                logger.info(f"Plot saved to {export_path / f'{self.name}_plot.html'}")
            elif export_path.exists() and not export_path.is_dir():
                raise NotADirectoryError("Provided path is not a directory")
            else:
                raise FileNotFoundError("Provided path does not exist")

    def _add_node_traces(self, fig, nodes_gdf, color_node_by):
        options = set(nodes_gdf[color_node_by.value])
        for option in options:
            filt_gdf = nodes_gdf[nodes_gdf[color_node_by.value] == option]
            text = [
                f"Name: {n} \nType: {t} \nPhases: {p} \nkV: {v}"
                for n, t, p, v in zip(filt_gdf.Name, filt_gdf.Type, filt_gdf.Phases, filt_gdf.kV)
            ]
            fig.add_trace(
                go.Scattergeo(
                    lon=filt_gdf.geometry.y,
                    lat=filt_gdf.geometry.x,
                    mode="markers",
                    hoverinfo=["lon", "lat", "text", "name"],
                    text=text,
                    name=f"Nodes - {color_node_by.value} - {option}",
                )
            )

    def _add_edge_traces(self, fig, edges_gdf, color_line_by):
        edge_options = set(edges_gdf[color_line_by.value])
        for edge_option in edge_options:
            filt_gdf = edges_gdf[edges_gdf[color_line_by.value] == edge_option]

            lats = []
            lons = []
            names = []
            types = []
            for feature, name, model_type in zip(filt_gdf.geometry, filt_gdf.Name, filt_gdf.Type):
                if isinstance(feature, shapely.geometry.linestring.LineString):
                    linestrings = [feature]
                elif isinstance(feature, shapely.geometry.multilinestring.MultiLineString):
                    linestrings = feature.geoms
                else:
                    continue
                for linestring in linestrings:
                    x, y = linestring.xy
                    lats = np.append(lats, y)
                    lons = np.append(lons, x)
                    types = np.append(types, [model_type] * len(y))
                    names = np.append(names, [f"Name: {name}, Type: {model_type}"] * len(y))
                    lats = np.append(lats, None)
                    lons = np.append(lons, None)
                    names = np.append(names, None)
                    types = np.append(types, None)

            fig.add_trace(
                go.Scattergeo(
                    lon=lons,
                    lat=lats,
                    mode="lines",
                    hoverinfo=["lon", "lat", "text", "name"],
                    text=names,
                    name=f"Edges -{color_line_by.value} - {edge_option}",
                )
            )

    @staticmethod
    def _map_strings_to_colors(strings):
        """Maps a list of strings to unique colors."""
        unique_strings = list(set(strings))  # Ensure uniqueness
        named_colors = pc.DEFAULT_PLOTLY_COLORS
        colors = {s: named_colors[i] for i, s in enumerate(unique_strings)}
        color_list = [colors[s] for s in strings]
        return color_list
