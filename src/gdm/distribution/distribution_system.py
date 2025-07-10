"""This module contains distribution system."""

from collections import defaultdict
from typing import Annotated, Type
import importlib.metadata
from pathlib import Path
import tempfile

from infrasys.time_series_models import TimeSeriesData, SingleTimeSeries
from shapely import Point, LineString, union_all
from infrasys import Component, System
from pydantic import BaseModel, Field
import plotly.graph_objects as go
from loguru import logger
import geopandas as gpd
import networkx as nx
import pandas as pd
import numpy as np
import shapely

from gdm.distribution.components.base.distribution_transformer_base import (
    DistributionTransformerBase,
)
from gdm.distribution.enums import Phase
from gdm.distribution.components import DistributionBus, GeometryBranch
from gdm.distribution.enums import ColorNodeBy, ColorLineBy
from gdm.distribution.components.base.distribution_branch_base import (
    DistributionBranchBase,
)
from gdm.distribution.components.distribution_transformer import (
    DistributionTransformer,
)
from gdm.distribution.components.distribution_vsource import (
    DistributionVoltageSource,
)
from gdm.exceptions import (
    MultipleOrEmptyVsourceFound,
)


class UserAttributes(BaseModel):
    """Data model for single time series data user attributes."""

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
        if not self.data_format_version:
            self.data_format_version = importlib.metadata.version("grid-data-models")

    def get_bus_connected_components(
        self, bus_name: str, component_type: Component
    ) -> list[Component] | None:
        """Retrieve components connected to a specified bus.

        This method returns a list of components of a specified type that are connected to a given bus
        within the distribution system. It checks for connections based on the presence of a 'bus' or
        'buses' field in the component model.

        Parameters
        ----------
        bus_name : str
            The name of the bus to which the components are connected.
        component_type : Component
            The type of components to search for connections.

        Returns
        -------
        list[Component] | None
            A list of components connected to the specified bus, or None if no components are found.

        Notes
        -----
        - The method filters components based on whether they have a direct connection to the specified
        bus, either through a single 'bus' field or a list of 'buses'.
        - This is useful for identifying all components that are directly associated with a particular
        bus in the distribution network.
        """

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
        """Retrieve model types containing a specific field type.

        This method identifies and returns a list of component model types that include a field
        with the specified type. It is useful for determining which models within the distribution
        system have fields of a particular component type.

        Parameters
        ----------
        field_type : Type[Component]
            The component type to search for within model fields.

        Returns
        -------
        list[Type[Component]]
            A list of model types that contain fields of the specified component type.

        Notes
        -----
        - The method iterates over all component types in the system and checks their fields
        for the specified type.
        - This can be used to identify models that have specific relationships or dependencies
        based on their field types.
        """
        return [
            model_type
            for model_type in self.get_component_types()
            if any(
                [field.annotation == field_type for _, field in model_type.model_fields.items()]
            )
        ]

    def get_source_bus(self) -> DistributionBus:
        """Identifies and returns the source bus of the distribution system.

        This method retrieves the distribution voltage source components and extracts the
        associated bus. It ensures that there is exactly one voltage source bus in the system,
        which serves as the starting point for power distribution.

        Returns
        -------
        DistributionBus
            The bus associated with the single distribution voltage source in the system.

        Raises
        ------
        MultipleOrEmptyVsourceFound
            If there are multiple or no voltage sources found in the system.

        Notes
        -----
        - The source bus is crucial for constructing directed graphs and analyzing power flow
        within the distribution network.
        """
        voltage_sources = self.get_components(DistributionVoltageSource)
        buses = [v_source.bus for v_source in voltage_sources]
        if len(buses) != 1:
            msg = f"Multiple or no vsource found for this system {buses}."
            raise MultipleOrEmptyVsourceFound(msg)
        return buses[0]

    def get_undirected_graph(self) -> nx.Graph:
        """Constructs an undirected graph representation of the distribution system.

        This method generates an undirected graph using NetworkX, where nodes represent distribution
        buses and edges represent connections between them. The graph is constructed by iterating
        over all distribution buses and their connecting branches and transformers.

        Returns
        -------
        nx.Graph
            An undirected graph representing the distribution system, with nodes as buses and edges
            as connections between them.

        Notes
        -----
        - The graph is useful for analyzing the connectivity and topology of the distribution network.
        - Each edge in the graph includes metadata such as the component's name and type.
        """
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

    def _add_to_subsystem(
        self,
        subtree_system: "DistributionSystem",
        parent_components: list[Component],
        bus_names: list[DistributionBus],
    ):
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

    def get_subsystem(
        self,
        bus_names: list[str],
        name: str,
        keep_timeseries: bool = False,
        time_series_type: Type[TimeSeriesData] = SingleTimeSeries,
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
        time_series_type: Type[TimeSeriesData]
            Type of time series data. Defaults to: SingleTimeSeries
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
            self._add_to_subsystem(subtree_system, parent_components, bus_names)

        for u in subtree.nodes():
            parent_components = self.list_parent_components(self.get_component(DistributionBus, u))
            self._add_to_subsystem(subtree_system, parent_components, bus_names)

        if keep_timeseries:
            for comp in subtree_system.get_components(
                Component,
                filter_func=lambda x: self.has_time_series(x, time_series_type=time_series_type),
            ):
                ts_metadata = self.list_time_series_metadata(
                    comp, time_series_type=time_series_type
                )
                for metadata in ts_metadata:
                    ts_data = self.get_time_series(
                        comp, metadata.variable_name, time_series_type=time_series_type
                    )
                    subtree_system.add_time_series(ts_data, comp, **metadata.user_attributes)

        return subtree_system

    def get_directed_graph(self) -> nx.DiGraph:
        """Constructs a directed graph representation of the distribution system.

        This method generates a directed graph using NetworkX, where nodes represent distribution
        buses and directed edges represent connections between them. The graph is constructed
        using a depth-first search (DFS) starting from the source bus, ensuring a hierarchical
        representation of the system.

        Returns
        -------
        nx.DiGraph
            A directed graph representing the distribution system, with nodes as buses and edges
            as connections between them.

        Notes
        -----
        - The source bus is determined using the `get_source_bus` method.
        - The directed graph is useful for analyzing the flow of electricity and identifying
        subsystems within the distribution network.
        """
        logger.info(f"Building directed graph for {self.name}")
        ugraph = self.get_undirected_graph()
        return nx.dfs_tree(ugraph, source=self.get_source_bus().name)

    def get_split_phase_mapping(self) -> dict[str, set[Phase]]:
        """Generates a mapping of components to their split-phase configurations.

        This method identifies distribution transformers with center-tapped windings and
        constructs a mapping of components in the low-voltage subsystem to the phases of
        the high-voltage bus. The mapping is useful for understanding the phase relationships
        in split-phase systems.

        Returns
        -------
        dict[str, set[Phase]]
            A dictionary where keys are component names and values are sets of phases
            associated with the high-voltage bus.

        Notes
        -----
        - The method uses the directed graph representation of the distribution system to
        identify subsystems connected to low-voltage buses.
        - Only transformers with center-tapped windings are considered for split-phase mapping.

        Logs
        ----
        - Logs the process of identifying and mapping split-phase transformers.
        """
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

    def _build_edge_geodataframe(self, graph) -> gpd.GeoDataFrame:
        """Returns geo dataframes for the edges

        Returns
        -------
        gpd.GeoDataFrame
           geodataframe with edge info
        """
        edge_data = defaultdict(list)
        for u, v, data in graph.edges(data=True):
            bus1 = self.get_component(DistributionBus, u)
            bus2 = self.get_component(DistributionBus, v)
            x1, x2 = bus1.coordinate.x, bus2.coordinate.x
            y1, y2 = bus1.coordinate.y, bus2.coordinate.y

            if not ((x1 == 0 and y1 == 0) or (x2 == 0 and y2 == 0)):
                component = self.get_component(data["type"], data["name"])
                if isinstance(component, DistributionTransformer):
                    phases = [",".join([phs.value for phs in w]) for w in component.winding_phases]
                    phases = "\n".join(phases)
                    length = 15.0
                else:
                    phases = ",".join([phs.value for phs in component.phases])
                    length = component.length.to("foot").magnitude
                edge_data["Phases"].append(phases)
                edge_data["Name"].append(data["name"])
                edge_data["Length"].append(length)
                edge_data["Type"].append(data["type"].__name__)
                edge_data["Latitude"].append([bus1.coordinate.y, bus2.coordinate.y])
                edge_data["Longitude"].append([x1, x2])

        edge_df = pd.DataFrame(edge_data)
        geometry = [
            LineString([Point(xy) for xy in zip(*xys)])
            for xys in zip(edge_df["Longitude"], edge_df["Latitude"])
        ]
        gdf_edges = gpd.GeoDataFrame(edge_df, geometry=geometry, crs="EPSG:4326")
        return gdf_edges

    def _build_node_geodataframe(self) -> gpd.GeoDataFrame:
        """
        Builds a GeoDataFrame containing node information for distribution buses.

        This method collects data from all distribution bus components, including
        their names, types, rated voltages, phases, and coordinates. It constructs
        a GeoDataFrame with this information, using the bus coordinates to create
        point geometries. The coordinate reference system (CRS) is determined from
        the bus data, defaulting to EPSG:4326 if not specified.

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame with node information and geometries.
        """
        node_data = defaultdict(list)
        system_crs = None
        for bus in self.get_components(DistributionBus):
            if bus.coordinate.x != 0 and bus.coordinate.y != 0:
                node_data["Name"].append(bus.name)
                node_data["Type"].append(DistributionBus.__name__)
                node_data["kV"].append(bus.rated_voltage.to("kilovolt").magnitude)
                node_data["Phases"].append(",".join([phs.value for phs in bus.phases]))
                node_data["Latitude"].append(bus.coordinate.y)
                node_data["Longitude"].append(bus.coordinate.x)
                system_crs = bus.coordinate.crs

        nodes_df = pd.DataFrame(node_data)
        gdf_nodes = gpd.GeoDataFrame(
            nodes_df,
            geometry=gpd.points_from_xy(nodes_df.Longitude, nodes_df.Latitude),
            crs="EPSG:4326" if system_crs is None else system_crs,
        )
        return gdf_nodes

    def to_gdf(self, export_file: Path | None = None) -> gpd.GeoDataFrame:
        """Converts the distribution system into a GeoDataFrame.

        This method constructs a GeoDataFrame representing the distribution system's nodes and edges,
        which can be used for geographic data analysis and visualization. The resulting GeoDataFrame
        includes spatial information and attributes for each component.

        Parameters
        ----------
        export_file : Path | None
            Optional path to save the GeoDataFrame as a CSV file. If None, the GeoDataFrame is not saved.

        Returns
        -------
        gpd.GeoDataFrame
            A GeoDataFrame containing the spatial and attribute data of the distribution system.

        Notes
        -----
        - The method uses the `_build_node_geodataframe` and `_build_edge_geodataframe` methods to
        construct the node and edge data, respectively.
        - The coordinate reference system is set to EPSG:4326 for compatibility with most geographic
        information systems.

        Logs
        ----
        - Logs the path where the GeoDataFrame is saved if `export_file` is provided.
        """
        graph = self.get_undirected_graph()
        nodes_gdf = self._build_node_geodataframe()
        edges_gdf = self._build_edge_geodataframe(graph)
        final_gdf = gpd.pd.concat([nodes_gdf, edges_gdf], ignore_index=True)

        if export_file:
            export_file = Path(export_file)
            final_gdf.to_csv(export_file)

        return final_gdf

    def to_geojson(self, export_file: Path | str) -> None:
        """Exports the distribution system to a GeoJSON file.

        This method converts the distribution system's components into a GeoDataFrame and
        writes it to a GeoJSON file at the specified path. The GeoJSON format is suitable
        for geographic data visualization and analysis.

        Parameters
        ----------
        export_file : Path | str
            The file path where the GeoJSON data will be saved.

        Raises
        ------
        FileNotFoundError
            If the specified export path does not exist.

        Notes
        -----
        - The method uses the `to_gdf` method to generate the GeoDataFrame representation
        of the distribution system.
        - The coordinate reference system is set to EPSG:4326 for compatibility with most
        geographic information systems.

        Logs
        ----
        - Logs the completion of the GeoJSON export process.
        """
        logger.info(f"Exporting GeoJSON to {export_file}")
        export_file = Path(export_file)
        system_gdf = self.to_gdf()
        with open(export_file, "w") as f:
            f.write(system_gdf.to_json())

    def plot(
        self,
        export_path: Path | None = None,
        zoom_level: int = 24,
        show: bool = True,
        color_node_by: ColorNodeBy = ColorNodeBy.PHASE,
        color_line_by: ColorLineBy = ColorLineBy.EQUIPMENT_TYPE,
        show_legend: bool = True,
        **kwargs,
    ) -> None:
        """Generates an interactive plot of the distribution system using Plotly.

        This method visualizes the distribution system's nodes and edges on a geographical map.
        Nodes and edges can be colored based on specified attributes, and the plot can be
        exported to an HTML file.

        Parameters
        ----------
        export_path : Path | None
            Directory path to save the plot as an HTML file. If None, the plot is not saved.
        zoom_level : int
            Zoom level for the map projection. Higher values zoom in closer.
        show : bool
            If True, displays the plot in a web browser.
        color_node_by : ColorNodeBy
            Attribute to color nodes by. Defaults to phase.
        color_line_by : ColorLineBy
            Attribute to color lines by. Defaults to equipment type.
        show_legend : bool
            If True, displays the legend on the plot.
        **kwargs
            Additional keyword arguments for customizing the plot's appearance.

        Raises
        ------
        NotADirectoryError
            If the provided export path is not a directory.
        FileNotFoundError
            If the provided export path does not exist.

        Notes
        -----
        - The plot uses the geographical center of the nodes for centering the map.
        - The coordinate reference system is set to EPSG:4326.
        - The plot is interactive and can be zoomed and panned.

        Logs
        ----
        - Logs the path where the plot is saved if `export_path` is provided.
        """

        system_gdf = self.to_gdf()

        nodes_gdf = system_gdf[system_gdf.Type == "DistributionBus"].copy()
        nodes_gdf["lon"] = nodes_gdf.geometry.y
        nodes_gdf["lat"] = nodes_gdf.geometry.x

        edges_gdf = system_gdf[system_gdf.Type != "DistributionBus"].copy()
        center = union_all(nodes_gdf.geometry).centroid

        fig = go.Figure()

        self._add_node_traces(fig, nodes_gdf, color_node_by)
        self._add_edge_traces(fig, edges_gdf, color_line_by)

        fig.update_layout(
            # title=f"GDM plot for {self.name} distribution system",
            geo=dict(
                center=dict(lat=center.x, lon=center.y),  # Set center
                projection_scale=zoom_level,  # Adjust zoom (lower value = more zoomed-in)
                showland=kwargs.get("showland", True),
                landcolor=kwargs.get("landcolor", "lightgray"),
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )

        if not show_legend:
            fig.update_layout(showlegend=False)

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
        if color_node_by == ColorNodeBy.DEFAULT:
            options = ["default"]
        else:
            options = set(nodes_gdf[color_node_by.value])
        for option in options:
            if option == "default":
                filt_gdf = nodes_gdf
            else:
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
        if color_line_by == ColorLineBy.DEFAULT:
            edge_options = ["default"]
        else:
            edge_options = set(edges_gdf[color_line_by.value])

        for edge_option in edge_options:
            if edge_option == "default":
                filt_gdf = edges_gdf
            else:
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

    def deepcopy(self) -> "DistributionSystem":
        """Returns a deep copy of the distribution system."""
        system = None
        with tempfile.TemporaryDirectory() as tmpdir:
            self.to_json(Path(tmpdir) / "test.json")
            system = DistributionSystem.from_json(Path(tmpdir) / "test.json")
            system.auto_add_composed_components = True

        # @dan how do i get this to work?

        # system = DistributionSystem(auto_add_composed_components=True)
        # for component in self.iter_all_components():
        #     new_component = self.deepcopy_component(component)
        #     system.add_component(new_component)

        return system

    def convert_geometry_to_matrix_representation(self):
        """Converts all GeometryBranch components in the distribution system to MatrixImpedanceBranch components.

        This method iterates over all GeometryBranch components in the system, converts each to its
        corresponding MatrixImpedanceBranch representation, and replaces the original component with
        the new one. The conversion process is logged, and the number of converted components is
        reported.

        Notes
        -----
        - The method temporarily sets `auto_add_composed_components` to True to facilitate the
        conversion process and restores it to its original state afterward.
        - The conversion is performed in-place, modifying the existing system.

        Logs
        ----
        - Logs the start of the conversion process.
        - Logs the number of GeometryBranch models converted to MatrixImpedanceBranch models.
        """

        logger.info("Converting models from GeometryBranch to MatrixImpedanceBranch...")
        auto_add = self.auto_add_composed_components
        self.auto_add_composed_components = True
        branches = list(self.get_components(GeometryBranch))
        for branch in branches:
            impedence_branch = branch.to_matrix_representation()
            self.remove_component(branch, cascade_down=True)
            self.add_component(impedence_branch)
        self.auto_add_composed_components = auto_add
        logger.info(f"GeometryBranch models converted -> {len(branches)}")
