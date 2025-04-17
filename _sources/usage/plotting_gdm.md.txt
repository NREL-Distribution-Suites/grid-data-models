(plotting_gdm)=
## Plotting GDM Models

The `DistributionSystem` class provides a method to plot the distribution system using Plotly. This method allows users to visualize the system's nodes and edges, which can be particularly useful for understanding the system's topology and identifying potential issues or opportunities for improvement. The plot can be saved as an HTML file for further analysis or sharing. The method also supports interactive exploration, allowing users to zoom in and out of the plot. Alternatively, users can use the `to_gdf` method to export the system's nodes and edges to a GeoDataFrame. Users can then call the `plot` method on the returned Geodataframe to create a stattic plot using Matplotlib.


### Function: `plot`

#### Description
Generates and optionally displays a plot of the distribution system using Plotly, with options to color nodes and edges based on specified criteria.

#### Parameters
- `export_path` (Path | None, optional): Directory path where the plot should be saved as an HTML file. If `None`, the plot is not saved.
- `zoom_level` (int, optional): The zoom level for the plot. Default is 24.
- `show` (bool, optional): Whether to display the plot. Default is `True`.
- `color_node_by` (ColorNodeBy, optional): Criteria for coloring nodes. Default is `ColorNodeBy.PHASE`.
- `color_line_by` (ColorLineBy, optional): Criteria for coloring edges. Default is `ColorLineBy.EQUIPMENT_TYPE`.
- `**kwargs`: Additional keyword arguments for customizing the plot's appearance.

#### Returns
- `None`

#### Usage
This function is used to visualize the distribution system, providing insights into its structure and characteristics. It supports interactive exploration and can be customized with various coloring options.


### Example 1: Building an interactive plot

```python
from gdm.distribution import DistributionSystem

system: DistributionSystem
system.plot()

```

<iframe src="../_static/plot_plotly.html" width="100%" height="500px" style="border:none;"></iframe>


### Example 2: Building a static plot

```python
from gdm.distribution import DistributionSystem
from matplotlib import pyplot as plt

system: DistributionSystem
gdf_df = system.to_gdf()
gdf_df.plot()
plt.show()
```

![Matplotlib example](./plot_mpl.PNG)