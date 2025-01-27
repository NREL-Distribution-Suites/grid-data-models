## Tracking changes in `grid-data-models`

The `grid-data-models` (GDM) package includes support for tracking temporal and scenario-driven changes in a distribution system model. Changes are enabled through property edits, equipment additions, and equipment deletions to a base GDM model at specific timestamps. Each modification is tracked and stored, ensuring a clear history of changes over time.

**Relevent GMD utility Functions:**

- `get_distribution_system_on_date`: Returns an updated GDM model with all modifications up to the specified `timestamp`.
- `get_distribution_system_for_scenario`: Applies all modifications related to a specific scenario to the base model.

### Example 1: Building a temporal model

In the following example,

1. We will make use of `gdmloader` package to fist download a sample GDM model. The package can be installed using `pip intall gdmloader`.

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

2. Next, We will build a catalog of components that will serve as an equipment library for additions to the base model and maps to temporal changes in the base model. In this catalog, we add two example models with fixed uuids that will later be used for temporal mapping

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

3. From the model, we get a line model and two load models. These components will be modified using the temporal changes mapping capability in this step.

```python
line_model_to_edit = base_model.get_component(MatrixImpedanceBranch, "fdr3_3_load_fdr3_3_load_4")
load_model_to_delete_in_2024 = base_model.get_component(DistributionLoad, "fdr2_load12")
load_model_to_delete_in_2025 = base_model.get_component(DistributionLoad, "fdr3_load15")
```

4. The `UpdateScenario` model in GDM represents a collection of system modifications. Each scenario object has a unique scenario name and a list of `SystemModification` objects, which represent individual modifications to be applied to a system. Each `SystemModification` object has a timestamp indicating when the modification was made along with a list of system additions, edits and deletions to be applied on the date.
   **additions**: This is a list attribute that holds the UUIDs of the components that were added in this modification. These UUIDs should exist in the `catalog`.
   **deletions**: This is a list attribute that holds the UUIDs of the components that were deleted in this modification. These UUIDs should exist in the `base system model`
   **edits**: This is a list attribute that holds the `PropertyEdit` objects that represent the edits made in this modification. `PropertyEdit` requires **name** of the property to be edited, the new **value** of the property and the **component_uuid** that maps to the modified component.

NOTE: When editing the property of an existing component, make sure to use properties that are in the component. For example, when modifying the length property of a distribution branch, PositiveDistance is used to define the new value in the example below:

<!--- Comment: this note begs a question. Is there any error checking for modifications to properties that are not in the component? -->

```python
from gdm.temporal_models import UpdateScenario, PropertyEdit, SystemModification

model_scenario =UpdateScenario(
    name = "Test scenario",
    modifications = [
        SystemModification(
            update_date="2022-01-01",
            edits=[
                PropertyEdit(
                    component_uuid=line_model_to_edit.uuid,
                    name="length",
                    value=PositiveDistance(200, "m"),
                )
            ],
        ),
        SystemModification(
            update_date="2023-01-01",
            additions=["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
        ),
        SystemModification(
            update_date="2024-01-01",
            deletions=[load_model_to_delete_in_2024.uuid],
        ),
        SystemModification(
            update_date="2025-01-01",
            deletions=[load_model_to_delete_in_2025.uuid],
        ),
    ] 
)
```

5. Finally, we use functions provided by the GDM library to apply changes to the base distribution system model.

```python
from datetime import date

from gdm.temporal_models import get_distribution_system_on_date

model_on_date= date(2024, 1, 1)
new_system = get_distribution_system_on_date(model_scenario, base_model, catalog, model_on_date)

```

Execution of the code block above returns the new distribution model with all changes applied for the date 2024/01/01. All changes applied to the base model are provided to the user in tabular form.

<!--- comment: Add a line explaining which function is called to create this table. -->

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

### Example 2: Working with multiple scenarios

1. In this example we create multiple scenarios, add them to a single system and serialize them to disk.

```python
system_scenarios = DistributionSystem(auto_add_composed_components=True)
system_scenarios.add_component(model_scenario)
model_scenario_2 = model_scenario.model_copy(
  update={
    'uuid': uuid4(),
    'name': 'scenario_2',
  }
)
system_scenarios.add_component(model_scenario_2)
system_scenarios.to_json("system_changes.json")
```

2. Once serialized, these components can be deserialized and retrieved similar to other components within a GDM system. One or more of the scenarios can then be applied to the base distribution system model.

```python
from gdm.temporal_models import UpdateScenario

system_scenarios = DistributionSystem.from_json("system_changes.json", auto_add_composed_components=True)
update_scenarios = list(system_scenarios.get_components(UpdateScenario))
for scenario in update_scenarios:
    print("Scenario name: ", scenario.name)

base_model: DistributionSystem  = loader.load_dataset(DistributionSystem, GDM_CASE_SOURCE.name, "three_feeder_switch")
base_model.auto_add_composed_components = True

model_on_date= date(2025, 1, 1)
new_system = get_distribution_system_on_date(update_scenarios[1], base_model, catalog, model_on_date)
```

Execution of code block above returns the new distribution model with all temporal changes applied unto 2025/01/01. All changes applied to the base model are provided to the user in tabular form.

```bash
Scenario name:  Test scenario
Scenario name:  scenario_2

                                Updates applied to system from scenario 'scenario_2'
┏━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  Timestamp ┃ Operation ┃                                 UUID ┃        Component Type ┃            Component Name ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 2022-01-01 │ Edit      │ c5923f11-7a13-42d2-8f3c-e4426e0eb9ab │ MatrixImpedanceBranch │ fdr3_3_load_fdr3_3_load_4 │
│ 2023-01-01 │ Addition  │ aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa │      DistributionLoad │         DistributionLoad1 │
│ 2024-01-01 │ Deletion  │ d295803d-d285-4096-bd2e-a05f7ea4f718 │      DistributionLoad │               fdr2_load12 │
│ 2025-01-01 │ Deletion  │ 630e59c7-fb0f-4da5-8312-2717b36380a0 │      DistributionLoad │               fdr3_load15 │
└────────────┴───────────┴──────────────────────────────────────┴───────────────────────┴───────────────────────────┘
```
