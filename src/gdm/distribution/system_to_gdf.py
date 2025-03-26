from collections import defaultdict

from shapely import Point, LineString

from gdm import (
    DistributionTransformer,
    DistributionBus,
)
import geopandas as gpd
import pandas as pd


class Converter:
    def __init__(self, distribution_system) -> None:
        self.system = distribution_system
        self.graph = distribution_system.get_undirected_graph()

    def build_node_geodataframe(self) -> gpd.GeoDataFrame:
        """Returns geo dataframes for the edges

        Returns
        -------
        gpd.GeoDataFrame
            geodataframe with node info
        """
        node_data = defaultdict(list)
        system_crs = None
        for bus in self.system.get_components(DistributionBus):
            if bus.coordinate.x != 0 and bus.coordinate.y != 0:
                node_data["Name"].append(bus.name)
                node_data["Type"].append(DistributionBus.__name__)
                node_data["kV"].append(bus.nominal_voltage.to("kilovolt").magnitude)
                node_data["Phases"].append(",".join([phs.value for phs in bus.phases]))
                node_data["Latitude"].append(bus.coordinate.y)
                node_data["Longitude"].append(bus.coordinate.x)
                system_crs = bus.coordinate.crs

        nodes_df = pd.DataFrame(node_data)
        gdf_nodes = gpd.GeoDataFrame(
            nodes_df,
            geometry=gpd.points_from_xy(nodes_df.Longitude, nodes_df.Latitude),
            crs="EPSG:4326" if system_crs is None else system_crs,
            # defaults to lat log coordinate system
        )
        return gdf_nodes

    def build_edge_geodataframe(self) -> gpd.GeoDataFrame:
        """Returns geo dataframes for the edges

        Returns
        -------
        gpd.GeoDataFrame
           geodataframe with edge info
        """
        edge_data = defaultdict(list)
        for u, v, data in self.graph.edges(data=True):
            bus1 = self.system.get_component(DistributionBus, u)
            bus2 = self.system.get_component(DistributionBus, v)
            x1, x2 = bus1.coordinate.x, bus2.coordinate.x
            y1, y2 = bus1.coordinate.y, bus2.coordinate.y

            if not ((x1 == 0 and y1 == 0) or (x2 == 0 and y2 == 0)):
                component = self.system.get_component(data["type"], data["name"])
                if isinstance(component, DistributionTransformer):
                    phases = [",".join([phs.value for phs in w]) for w in component.winding_phases]
                    phases = "\n".join(phases)
                    length = 5.0
                else:
                    phases = ",".join([phs.value for phs in component.phases])
                    length = component.length.to("foot").magnitude
                edge_data["Phases"].append(phases)
                edge_data["Name"].append(data["name"])
                edge_data["Length"].append(length)
                edge_data["Type"].append(data["type"].__name__)
                edge_data["Latitude"].append([x1, x2])
                edge_data["Longitude"].append([bus1.coordinate.y, bus2.coordinate.y])

        edge_df = pd.DataFrame(edge_data)
        geometry = [
            LineString([Point(xy) for xy in zip(*xys)])
            for xys in zip(edge_df["Longitude"], edge_df["Latitude"])
        ]
        gdf_edges = gpd.GeoDataFrame(edge_df, geometry=geometry, crs="EPSG:4326")
        return gdf_edges

    def build_dataframes(self) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """Converts gdm model to geopandas dataframes

        Returns
        -------
        tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]
            Returns geodataframes first one for the nodes and the seond one for the edges
        """

        return self.build_node_geodataframe(), self.build_edge_geodataframe()
