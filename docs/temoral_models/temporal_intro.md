## Temporal models in `grid-data-models`

The `grid-data-models` (GDM) package includes comprehensive support for modeling temporal changes within a distribution system. This functionality allows users to effectively manage time-dependent modifications to a base grid model, enabling dynamic analysis and scenario planning. All temporal changes are built upon a single base GDM model, ensuring a consistent foundation for analysis.
  

### Key Concepts

1. **Time-Stamped Modifications**:  
   The system enables edits, additions, and deletions to a base GDM model at specific timestamps. Each modification is tracked and stored, ensuring a clear history of changes over time.

2. **Scenario-Based Temporal Modeling**:  
   Users can define multiple temporal scenarios linked to the same base model. This feature allows for maintaining and analyzing various operational or planning conditions within a single system, avoiding duplication of base models.

3. **Efficient Retrieval**:  
   With exposed utility functions, users can easily retrieve an updated GDM model for any given timestamp. The retrieved model reflects all modifications up to the specified time, providing a complete and consistent view of the system.

4. **Scenario Management**:  
  Temporal changes can be grouped into scenarios, enabling users to manage different operational cases independently while sharing a common base model.

**Relevent GMD Utility Functions:**
  - `get_distribution_system_on_date(date, scenario_id)`: Returns the GDM model updated to include all changes up to the specified `timestamp`.
  - `get_distribution_system_for scenario(scenario_id)`: Applies all  modifications related to a specific scenario to the base model.


###  Example for Temporal Modeling Usage

In the following example, 

1. We will Make use of `gdmloader` package to fist download a sample GDM model. The package can be installed using `pip intall gdmloader`. From the model, we get a line model and two load models. These components will later be modified using the temporal changes mapping capability.

```python 
from gdm import DistributionSystem, DistributionLoad, DistributionSolar, MatrixImpedanceBranch
from gdm.quantities import PositiveDistance
from gdmloader.constants import GDM_CASE_SOURCE
from gdmloader.source import SystemLoader

loader = SystemLoader()
loader.add_source(GDM_CASE_SOURCE)
base_model: DistributionSystem  = loader.load_dataset(DistributionSystem, GDM_CASE_SOURCE.name, "three_feeder_switch")
base_model.auto_add_composed_components = True

line_model_to_edit = base_model.get_component(MatrixImpedanceBranch, "fdr3_3_load_fdr3_3_load_4")
load_model_to_delete_in_2024 = base_model.get_component(DistributionLoad, "fdr2_load12")
load_model_to_delete_in_2025 = base_model.get_component(DistributionLoad, "fdr3_load15")

```

2. Next, We will build a catalog of components that will serve as a equipment library for additions to the base model and maps to temporal changes in the base model. In this catalog, we add two examples models with fixed uuids that will later be used for temporal mapping

```python 
from uuid import UUID

catalog = DistributionSystem(auto_add_composed_components=True)
# Model to edit in 2022 
catalog.add_component(
    DistributionLoad.example().model_copy(update={'uuid': UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')})
) 
catalog.add_component(
    DistributionSolar.example().model_copy(update={'uuid': UUID('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb')})
) 
```

3. In the next step, we build a list of temporal changes that apply to the base model. Model additions map to models in the calalog. Make sure that the UUIDs for model additions map to models in the build catalog. 


NOTE: When editing property of an existing component, make sure to use the same quantity as defined in the model defination. For example when modifing the length property of a distribution branch, PositiveDistance is used to the define the new value


```python 
from gdm.temporal_models import UpdateScenario, PropertyEdit, SystemModifiaction

model_scenario =UpdateScenario(
    name = "Test scenario",
    system_modifications = [
        SystemModifiaction(
            update_date="2022-01-01",
            edits=[
                PropertyEdit(
                    component_uuid=line_model_to_edit.uuid,
                    name="length",
                    value=PositiveDistance(200, "m"),
                )
            ],
        ),
        SystemModifiaction(
            update_date="2023-01-01",
            additions=["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
        ),
        SystemModifiaction(
            update_date="2024-01-01",
            deletions=[load_model_to_delete_in_2024.uuid],
        ),
        SystemModifiaction(
            update_date="2025-01-01",
            deletions=[load_model_to_delete_in_2025.uuid],
        ),
    ] 
)
```

Finally, we use functions provided by the GDM library to apply changes to the base distribution system model. 
```python 
from datetime import date

from gdm.temporal_models import get_distribution_system_on_date

model_on_date= date(2024, 1, 1)
new_system = get_distribution_system_on_date(model_scenario, base_model, catalog, model_on_date)

```

Execution of code block above returns the new distribution model with all temporal changes applied unto 24/01/01. All changes applied to the base model are provided to the use in tabular form.


```bash
                               Updates applied to system from scenario 'Test scenario'
┏━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  Timestamp ┃ Operation ┃                                 UUID ┃        Component Type ┃            Component Name ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 2022-01-01 │ Edit      │ c5923f11-7a13-42d2-8f3c-e4426e0eb9ab │ MatrixImpedanceBranch │ fdr3_3_load_fdr3_3_load_4 │
│ 2023-01-01 │ Addition  │ aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa │      DistributionLoad │         DistributionLoad1 │
│ 2024-01-01 │ Deletion  │ d295803d-d285-4096-bd2e-a05f7ea4f718 │      DistributionLoad │               fdr2_load12 │
└────────────┴───────────┴──────────────────────────────────────┴───────────────────────┴───────────────────────────┘
```
