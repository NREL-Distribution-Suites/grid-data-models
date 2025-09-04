

[![Upload to PyPi](https://github.com/NREL-Distribution-Suites/grid-data-models/actions/workflows/publish_to_pypi.yml/badge.svg)](https://github.com/NREL-Distribution-Suites/grid-data-models/actions/workflows/publish_to_pypi.yml) •  [![Pytest](https://github.com/NREL-Distribution-Suites/grid-data-models/actions/workflows/pull_request_tests.yml/badge.svg)](https://github.com/NREL-Distribution-Suites/grid-data-models/actions/workflows/pull_request_tests.yml) •  [![deploy-book](https://github.com/NREL-Distribution-Suites/grid-data-models/actions/workflows/deploy.yml/badge.svg)](https://github.com/NREL-Distribution-Suites/grid-data-models/actions/workflows/deploy.yml) • ![PyPI - Downloads](https://img.shields.io/pypi/dm/grid-data-models) •  [![codecov](https://codecov.io/github/NREL-Distribution-Suites/grid-data-models/branch/main/graph/badge.svg?token=K0X11EXOX8)](https://codecov.io/github/NREL-Distribution-Suites/grid-data-models) •  [![CodeFactor](https://www.codefactor.io/repository/github/nrel-distribution-suites/grid-data-models/badge)](https://www.codefactor.io/repository/github/nrel-distribution-suites/grid-data-models)

# Grid Data Models (GDM)

GDM is a python package containing data models for power system assets and datasets. This package is actively being developed at [National Renewable Energy Laboratory (NREL)](https://www.nrel.gov/).

## Installation

You can install the latest version of `grid-data-models` from PyPi.

```bash
pip install grid-data-models
```

## Why Grid Data Models?

In an effort to reduce code duplication and provide client packages a standard interface to interact with power system data, a group of research engineers at NREL is working on developing standard data models. Features:

- **Built-in validation layer:** Use of [pydantic](https://docs.pydantic.dev/latest/) allows us to validate model fields.
- **Time series data management:** GDM uses [infrasys](https://github.nrel.gov/CADET/infrastructure_systems) package which enables [efficient time series data management](https://nrel.github.io/infrasys/explanation/time_series.html) by sharing arrays across components and offloading system memory. For example, we can attach time series power consumption data to a load profile.
- **Built-in unit conversion:** GDM leverages [pint](https://pint.readthedocs.io/en/stable/) for unit conversion for power system quantities. For example, power, voltage, time, etc.
- **JSON serialization/deserialization:** GDM uses [infrasys](https://github.com/NREL/infrasys) to serialize and deserialize distribution system components to/from JSON.
- **Track System Changes:** Supports tracking changes within a distribution model (both temporal and scenario-based static updates), enabling powerful scenario management capabilities.
- **Graph-Based Analysis:** Exposes a connectivity graph using NetworkX, allowing advanced graph-based algorithms and visualizations.
- **Interoperability:** Easily integrates with existing tools.
- **Model reduction:** Built-in support for multiple model reduction algorithms.

## How to get started?

To get started, you can clone and pip install this library from [here](https://nrel-distribution-suites.github.io/grid-data-models/).


## Contributors

- **Kapil Duwadi**
- **Aadil Latif**
- **Tarek Elgindy**
- **Pedro Andres Sanchez Perez**
- **Daniel Thom**
- **Jeremy Keen**
