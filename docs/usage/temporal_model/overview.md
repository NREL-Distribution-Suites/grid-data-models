(temporal-changes)=
## Tracking changes in GDM

The `grid-data-models` (GDM) package includes comprehensive support for modeling temporal changes within a distribution system. This functionality allows users to effectively manage tracked changes to a base grid model, enabling dynamic analysis and scenario planning. All tracked changes are built upon a single base GDM model, ensuring a consistent foundation for analysis. The system enables edits, additions, and deletions to a base GDM model at specific timestamps. Each modification is tracked and stored, ensuring a clear history of changes over time.
  
**Relevent GMD utility Classed and Functions :**
  - `TrackedChange`: A class that represents a tracked change to a system. It includes attributes for the date scenario name, changes are applied, the list of additions, edits, and deletions.
  - `apply_updates_to_system`: Takes in a list of `TrackedChange` objects and returns the GDM model updated to include all changes.
  - `filter_tracked_changes_by_name_and_date`: Helper function that enables users to filter a list of `TrackedChange` objects base on scenario_name and / or date of interest.


###  Example: Building a temporal model 

In the following example, 

1. We will Make use of `gdmloader` package to fist download a sample GDM model. The package can be installed using `pip intall gdmloader`. 

```python 
from gdm import DistributionSystem, DistributionLoad, DistributionSolar, MatrixImpedanceBranch
from gdm.quantities import PositiveDistance
from gdmloader.constants import GDM_CASE_SOURCE
from gdmloader.source import SystemLoader

loader = SystemLoader()
loader.add_source(GDM_CASE_SOURCE)
base_model: DistributionSystem  = loader.load_dataset(DistributionSystem, GDM_CASE_SOURCE.name, "three_feeder_switch")
base_model.auto_add_composed_components = True

```

2. Next, We will build a catalog of components that will serve as a equipment library for additions to the base model and maps to temporal changes in the base model. In this catalog, we add two examples models with fixed uuids that will later be used for temporal mapping

```python 
from uuid import UUID, uuid4

catalog = DistributionSystem(auto_add_composed_components=True)
# Model to edit in 2022 
catalog.add_component(
    DistributionLoad.example().model_copy(update={'uuid': UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')})
) 
catalog.add_component(
    DistributionSolar.example().model_copy(update={'uuid': UUID('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb')})
) 
```

3. From the model, we get a line model and two load models. These components will be modified to reflect changes in the base model. 
 
```python 
line_model_to_edit = base_model.get_component(MatrixImpedanceBranch, "fdr3_3_load_fdr3_3_load_4")
load_model_to_delete_in_2024 = base_model.get_component(DistributionLoad, "fdr2_load12")
load_model_to_delete_in_2025 = base_model.get_component(DistributionLoad, "fdr3_load15")
```


4. Each `TrackedChange` object has a scenario name. Additionally, this object may also have a date field that can be used to filter changes based on specific dates. Each `TrackedChange` has a list of system additions, edits and deletions to be applied on the date.

- **additions**: This is a list attribute that holds the UUIDs of the components that were added in this modification. These UUIDs should exist in the `catalog`.
- **deletions**: This is a list attribute that holds the UUIDs of the components that were deleted in this modification. These UUIDs should exist in the `base system model`
- **edits**: This is a list attribute that holds the `PropertyEdit` objects that represent the edits made in this modification. `PropertyEdit` requires **name** of the property to be edited, the new **value** of the property and the **component_uuid** that maps to the modified component. 

NOTE: When editing property of an existing component, make sure to use the same quantity / component type as defined in the model defination. For example when modifing the length property of a distribution branch, PositiveDistance is used to the define the new value in the example below

```python 
from gdm.temporal_models import UpdateScenario, PropertyEdit, TrackedChange

update_scenario = [
    TrackedChange(
        scenario_name="scenario_1",
        update_date="2022-01-01",
        edits=[
            PropertyEdit(
                component_uuid=capacitor.uuid,
                name="rated_reactive_power",
                value=PositiveReactivePower(200, "kvar"),
            )
        ],
    ),
    TrackedChange(
        scenario_name="scenario_1",
        update_date="2023-01-01",
        additions=["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
    ),
    TrackedChange(
        scenario_name="scenario_1",
        update_date="2024-01-01",
        deletions=[load1.uuid],
    ),
    TrackedChange(
        scenario_name="scenario_2",
        update_date="2025-01-01",
        deletions=[load2.uuid],
    ),
]
```

5. Next, we usse `filter_tracked_changes_by_name_and_date` to filter a list of tracked changes based on a specific scenario name and / or update date.

```python
tracked_changes = filter_tracked_changes_by_name_and_date(
    tracked_changes,
    scenario_name="scenario_1",
    update_date=datetime.strptime("2022-1-1", "%Y-%m-%d").date(),
)
```


6. Finally, we use functions provided by the GDM library to apply changes to the base distribution system model. 
```python 
from datetime import date

from gdm.temporal_models import apply_updates_to_system

model_on_date= date(2024, 1, 1)
new_system = apply_updates_to_system(
    tracked_changes=tracked_changes, system=system, catalog=catalog
)
```

Execution of code block above returns the new distribution model with all temporal changes applied unto 2024/01/01. All changes applied to the base model are provided to the use in tabular form.


```bash
                                                         Updates applied to the system
┏━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃  Timestamp ┃ Operation ┃                                 UUID ┃          Component Type ┃      Component Name ┃ Connected bus ┃   Scenario ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 2022-01-01 │ Edit      │ ce5f1242-9e2f-46df-b20c-d6032eababe5 │ PhaseCapacitorEquipment │ phase_capacitor_0_4 │          None │ scenario_1 │
└────────────┴───────────┴──────────────────────────────────────┴─────────────────────────┴─────────────────────┴───────────────┴────────────┘
```

Note: We can alternately filter tracked changes based on just the scenario name. 

```python
tracked_changes = filter_tracked_changes_by_name_and_date(
    tracked_changes,
    scenario_name="scenario_1",
)
```

Using the following filtering function above returns 

```bash
                                                           Updates applied to the system
┏━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃  Timestamp ┃ Operation ┃                                 UUID ┃          Component Type ┃         Component Name ┃ Connected bus ┃   Scenario ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 2022-01-01 │ Edit      │ 050b6713-8ef9-44d5-b7c2-8ef7ceb5bc0f │ PhaseCapacitorEquipment │    phase_capacitor_0_4 │          None │ scenario_1 │
│ 2023-01-01 │ Addition  │ aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa │           LoadEquipment │ added_phase_load_model │          None │ scenario_1 │
│ 2024-01-01 │ Deletion  │ a5f728f3-df2a-4581-bd6a-6274b02bf63c │        DistributionLoad │                 load_5 │         bus_5 │ scenario_1 │
└────────────┴───────────┴──────────────────────────────────────┴─────────────────────────┴────────────────────────┴───────────────┴────────────┘
```
