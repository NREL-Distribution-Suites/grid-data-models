---
title: 'Grid-Data-Models (GDM): Standardized, Unit-Aware Data Models for Distribution System Modeling and Interoperability.'
tags:
  - python
  - power distribution systems
  - data models
  - model reduction
  - time-series
  - unit-aware
  - tracked chanegs

authors:
  - name: Aadil Latif
    orcid: 0000-0002-0805-3866
    affiliation: 1
  - name: Kapil Duwadi
    orcid: 0000-0002-0589-5187
    affiliation: 1
  - name: Tarek Elgindy
    affiliation: 1
  - name: Jeremy Keen
    affiliation: 1
  - name: Pedro Andrés Sánchez Pérez
    affiliation: 1
  - name: Daniel Thom
    affiliation: 1

affiliations:
 - name: National Renewable Energy Laboratory (NREL), Golden, CO, USA
   index: 1
date: 30 July 2025
bibliography: paper.bib

---

### Summary

[`Grid-Data-Models` (GDM)](https://github.com/NREL-Distribution-Suites/grid-data-models) is a Python package that provides a suite of validated, extensible, and unit-aware data schemas for modeling electric power distribution systems. This package is designed to support interoperability, scenario-driven planning, and integration with simulation workflows. The models include electric system elements such as buses, transformers, switches, distributed energy resources (DERs), and associated time-series datasets like load profiles or solar irradiance profiles.

GDM models are defined using Pydantic [@Colvin_Pydantic_Validation_2025], enforce physical unit consistency using [Pint](https://pint.readthedocs.io), and support JSON-serializable scenarios with versioned change tracking. GDM exposes the physical network structure as a [NetworkX](https://networkx.org/) graph, enabling analysis and model reduction. GDM aims to standardize data handling at NREL’s distribution modeling ecosystem ( @osti_code-74722 , @osti_code-20924 , @osti_code-95577 ,  @osti_code-147712 ) , while also being reusable by the broader power systems research community.


### Statement of Need


Industry standards like the Common Information Model (CIM) from the @IEC61968-11 and MultiSpeak [@osti_1644250] have been developed to facilitate data exchange and interoperability between utility systems. CIM provides a comprehensive object model for electric system data, while MultiSpeak focuses on integration between utility operations. Working with CIM can be a bit challenging, given the complex ontology of power systems and possibility of circular referencing within CIM models. @mukherjee2020cim developed CIMhub to streamline the extraction, conversion, and validation of distribution data, though CIMhub itself requires a complex setup and configuration process. @osti_code-127055 in their recent work, introduced CIMGraph, a Python package for CIM distribution data models, with focus on improving user experience.


One key difference between CIM and GDM is that, unlike CIM, GDM not only validates data models but also explicitly checks connectivity among electrical components. This ensures that the network structure and relationships between elements are correct and consistent, which is essential for reliable analysis and scenario modeling.


In addition to interoperability and validation, GDM fulfills further needs in distribution system modeling:

- **Model reduction capabilities**: GDM enables users to simplify and analyze network topologies, supporting planning and operational studies that require reduced or segmented models.
- **Tracked changes on base models**: GDM allows users to represent evolving system states over simulated time, making it possible to encode incremental changes for resilience and capacity expansion studies where the network configuration and assets change as scenarios progress.

`Grid-Data-Models` addresses these needs by offering a unified data representation framework with robust validation, units, connectivity, and change tracking. It enables consistent model building and exchange across workflows, and simplifies scenario studies by allowing deltas and branching models.


### Key Features

GDM offers a comprehensive suite of features for distribution system modeling. Every physical field is validated and unit-consistent through Pydantic and Pint integration, with clear exceptions for invalid or mismatched values. The 'tracked changes' feature enables users to encode both temporal and non-temporal modifications incrementally, supporting model versioning and diffing, thus enabling users to model an evolving system. 

Full network connectivity can be exported as a NetworkX graph, facilitating topology-based operations such as feeder segmentation, load aggregation and model reduction. Time-series integration is achieved via shared array references using the [infrasys](https://github.com/NREL/infrasys) package, efficiently managing repeated load or PV profiles. The package also supports clean serialization / deserialization of data models and mapped time-series data.

Supporting packages like [GDMloader](https://github.com/NREL-Distribution-Suites/gdmloader) allow users to seamlessly load, manage, and share models hosted in cloud infrastructure, enabling collaborative workflows and scalable data access. GDMloader also provides an extensible component library with over 25000 electrical equipment definations, making it easy to reuse equipment definations or control schemes as research needs evolve.

Built-in versioned change tracking ensures reproducible scenario analysis and historical audits, while integration with NREL tools such as SHIFT and DiTTo streamlines data exchange and workflow automation. Starting v2.0,0, backward compatibility is maintained, ensuring legacy data and workflows remain usable as the package evolves.

GDM's lightweight, pure-Python design makes it ideal for research prototyping, teaching, and data curation. The package includes a full validation test suite and serialization tests using GitHub Actions, is actively maintained with frequent releases, and features a community-driven roadmap for ongoing extension and improvement.


### Example Usage

```python
from infrasys import Location

from gdm.distribution.enums import LimitType, Phase, VoltageTypes
from gdm.distribution.components.base.distribution_component_base 
from gdm.distribution.common.limitset import VoltageLimitSet
from gdm.distribution.components import DistributionBus
from gdm.quantities import Voltage

DistributionBus(
            voltage_type=VoltageTypes.LINE_TO_LINE,
            phases=[Phase.A, Phase.B, Phase.C],
            rated_voltage=Voltage(400, "volt"),
            name="DistBus1",
            voltagelimits=[
                VoltageLimitSet(limit_type=LimitType.MIN, value=Voltage(400 * 0.9, "volt")),
                VoltageLimitSet(limit_type=LimitType.MAX, value=Voltage(400 * 1.1, "volt")),
            ],
            coordinate=Location(x=20.0, y=30.0),
        )
```



This simple example illustrates strongly typed and unit-aware component creation. Users can then attach time-series data, serialize models, apply tracked changes, or export the network graph.


# Next Steps

In the next minor release, we intend to add data models for aggregators, tariffs, and consumers, expanding the scope of GDM to better support market modeling. There is also ongoing work on the development of structural models, such as poles, crossarms, and conduits. These models are needed to improve resilience analysis capabilities and enable more detailed representation of physical infrastructure in distribution systems.


# Acknowledgements

This work was authored by the National Renewable Energy Laboratory (NREL), operated by Alliance for Sustainable Energy, LLC, for the U.S. Department of Energy (DOE) under Contract No. DE-AC36-08GO28308. Funding provided by NREL license revenue under the provisions of the Bayh-Dole Act. The views expressed in the article do not necessarily represent the views of the DOE or the U.S. Government. The U.S. Government retains and the publisher, by accepting the article for publication, acknowledges that the U.S. Government retains a nonexclusive, paid-up, irrevocable, worldwide license to publish or reproduce the published form of this work, or allow others to do so, for U.S. Government purposes.


# References
