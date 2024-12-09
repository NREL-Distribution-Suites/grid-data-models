## Temporal models in `grid-data-models`

The `grid-data-models` (GDM) package includes comprehensive support for modeling temporal changes within a distribution system. This functionality allows users to effectively manage time-dependent modifications to a base grid model, enabling dynamic analysis and scenario planning.

### Key Concepts

1. **Time-Stamped Modifications**:  
   The system enables edits, additions, and deletions to a base GDM model at specific timestamps. Each modification is tracked and stored, ensuring a clear history of changes over time.

2. **Scenario-Based Temporal Modeling**:  
   Users can define multiple temporal scenarios linked to the same base model. This feature allows for maintaining and analyzing various operational or planning conditions within a single system, avoiding duplication of base models.

3. **Efficient Retrieval**:  
   With exposed utility functions, users can easily retrieve an updated GDM model for any given timestamp. The retrieved model reflects all modifications up to the specified time, providing a complete and consistent view of the system.

### Implementation Features
- **Base Model Integrity**:  
  All temporal changes are built upon a single base GDM model, ensuring a consistent foundation for analysis.
  
- **Scenario Management**:  
  Temporal changes can be grouped into scenarios, enabling users to manage different operational cases independently while sharing a common base model.

- **Utility Functions**:  
  - `get_model_at_time(timestamp)`: Returns the GDM model updated to include all changes up to the specified `timestamp`.
  - `apply_scenario(scenario_id)`: Applies all temporal modifications related to a specific scenario to the base model.
  - `list_scenarios()`: Lists all defined scenarios for the base model.

### Example Usage
```python

```

This capability allows users to seamlessly integrate time-dependent changes into their workflows, making `grid-data-models` a powerful tool for both operational and planning purposes in distribution system analysis.