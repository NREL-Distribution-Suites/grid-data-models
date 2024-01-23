from infrasys.component_models import Component


class DistributionAdmittanceMatrix(Component):
    y_bus_real: list[float]
    y_bus_imag: list[float]
    indices: list[int]
    indptr: list[int]
    node_order: list[str]

    @classmethod
    def example(cls):
        return DistributionAdmittanceMatrix(
            y_bus_real=list(range(4)),
            y_bus_imag=list(range(4)),
            indices=list(range(4)),
            indptr=list(range(2)),
            node_order=["n1", "n2"],
        )
