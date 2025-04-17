
(gis_support)=
## Exporting to GIS formats
---

The `DistributionSystem` class provides methods to support export to GIS data formats. This functionality is particularly useful for integrating distribution systems with GIS-based mapping and analysis tools. Two format options are available: `to_gdf` and `to_geojson`. These functions convert the distribution system's nodes and edges into a GeoDataFrame (GDF) and optionally export it to a CSV or JSON file, respectively.


### Function: `to_gdf`

#### Description
Converts the distribution system's nodes and edges into a GeoDataFrame (GDF) and optionally exports it to a CSV file.

#### Parameters
- `export_file` (Path | None, optional): The file path where the GDF should be exported as a CSV. If `None`, the GDF is not exported.

#### Returns
- `gpd.GeoDataFrame`: A GeoDataFrame containing both nodes and edges of the distribution system.

#### Usage
This function is useful for obtaining a spatial representation of the distribution system, which can be further used for analysis or visualization.

---

### Function: `to_geojson`

#### Description
Exports the distribution system's GDF to a GeoJSON file.

#### Parameters
- `export_file` (Path | str): The file path where the GeoJSON should be saved.

#### Returns
- `None`

#### Usage
This function is used to create a GeoJSON file, which is a widely-used format for representing geographical features and can be used in various GIS applications.

