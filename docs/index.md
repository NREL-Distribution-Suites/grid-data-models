# Grid Data Models (GDM)

GDM is a python package containing [pydantic](https://docs.pydantic.dev/latest/) data models for power system assets and datasets. This package is actively being developed at [National Renewable Energy Laboratory (NREL)](https://www.nrel.gov/) and intended to be open sourced in the future.

## Why Grid Data Models ?

In an effort to reduce code duplication and provide client packages a standard interface to interact with power system data, a group of 
research engineers at NREL is working on developing standard data models. Features:

- **Builtin validation layer:** Use of [pydantic](https://docs.pydantic.dev/latest/) in creating data models allows us to check for fields during the time of construction and update.
- **Timeseries data management:** GDM uses [infrasys](https://github.nrel.gov/CADET/infrastructure_systems) package which enables attaching time series data to fields in the data model. For example, we can attach time series power consumption data to a load profile.
- **Builtin unit conversion:** GDM leverages [pint](https://pint.readthedocs.io/en/stable/) for unit conversion for power system quantities. For e.g power, voltage, time etc.
- **JSON serialization/deserializatin:** GDM uses [infrasys](https://github.nrel.gov/CADET/infrastructure_systems) to serialize and deserialize distribution system containing power system components and time series data attached to components.

## How to get started ?

To get started, you can clone and pip install this library from [here](https://github.nrel.gov/CADET/grid-data-models).


## Contributors

- **Kapil Duwadi**
- **Tarek Elgindy**
- **Aadil Latif**
- **Daniel Thompson**
- **Jeremy Keen**


```{toctree}
:caption: Getting Started
:hidden: true

install.md
```

```{toctree}
:caption: API Documentation
:hidden: true
:toc-depth: 0

api/distribution_bus.md
api/distribution_branch.md
api/distribution_capacitor.md
api/distribution_load.md
api/distribution_transformer.md
api/distribution_wires.md
api/distribution_vsource.md
api/limitset.md
api/distribution_enum.md
api/distribution_component.md
api/quantities
```
