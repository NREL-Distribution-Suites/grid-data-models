# Model reduction

The grid-data-models (GDM) package provides helper functions to facilitate the reduction of distribution models, making them more computationally efficient for specific analyses. Model reduction techniques are particularly useful when studying large distribution networks where simulating the entire model is unnecessary or resource-intensive.

GDM's model reduction helpers allow users to:

* **Simplify Topologies:** Collapse sections of the network, such as radial feeders, to their equivalent representations.
* **Aggregate Loads and Generators:** Combine multiple loads or distributed energy resources (DERs) into single equivalent elements.
* **Maintain Connectivity Integrity:** Ensure reduced models remain electrically consistent, adhering to the connectivity validation framework built into GDM.

Model reduction is especially valuable when applied to optimization problems, where it helps reduce computational times by minimizing the size and complexity of the models being optimized. This allows researchers and engineers to obtain faster solutions while preserving the accuracy of essential model dynamics.

GDM currently supports two model reduction formulations:

## Three-Phase Balanced Representation

In this approach, the model is reduced by representing only the three-phase buses in the system. This formulation is particularly useful when focusing on system-level studies where maintaining a balanced representation of the network is sufficient.

```python
from gdm.distribution.network.reducer import reduce_to_three_phase_system
from gdm import DistributionSystem

gdm_sys: DistributionSystem = DistributionSystem.from_json("<PATH TO YOUR GDM MODEL>")
three_phase_gdm_model: DistributionSystem = reduce_to_three_phase_system(
    gdm_sys, 
    name="reduced_system", 
    agg_timeseries=False
)

```

## Primary Network Representation

This approach involves lumping loads, generation, and capacitors and representing them on the primary network. All secondary networks are removed, resulting in a streamlined model that captures the essential characteristics of the primary distribution network while discarding unnecessary details.

```python
from gdm.distribution.network.reducer import reduce_to_primary_system
from gdm import DistributionSystem

gdm_sys: DistributionSystem = DistributionSystem.from_json("<PATH TO YOUR GDM MODEL>")
primary_gdm_model: DistributionSystem = reduce_to_primary_system(
    gdm_sys, 
    name="reduced_system", 
    agg_timeseries=False
)
```

## Support for timeseries aggregation

An additional feature of GDM’s model reduction framework is the ability to represent aggregated time series data in the reduced models for GDM models that have time series data. This ensures that temporal dynamics are preserved even when the network is simplified, allowing for accurate performance analysis over time. To aggregate timeseries data users should set `agg_timeseries` to  `True`
and additionally, set the `time_series_type` field to either `SingleTimeSeries` or `NonSequentialTimeSeries` (depending on the type of profiles used to build the GDM model). 

```python
from infrasys.time_series_models import SingleTimeSeries

from gdm.distribution.network.reducer import reduce_to_three_phase_system
from gdm import DistributionSystem

gdm_sys: DistributionSystem = DistributionSystem.from_json("<PATH TO YOUR GDM MODEL>")
three_phase_gdm_model: DistributionSystem = reduce_to_three_phase_system(
    gdm_sys, 
    name="reduced_system", 
    agg_timeseries=True, 
    time_series_type=SingleTimeSeries
)

```
