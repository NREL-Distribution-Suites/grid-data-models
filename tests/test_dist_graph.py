from gdm import DistributionGraph, DistributionModel


def test_graph_creation():
    dist_model = DistributionModel.example()
    graph_instance = DistributionGraph(dist_model)

    if len(graph_instance.graph.nodes) != len(dist_model.buses):
        msg = f"Number of nodes in graph {len(graph_instance.graph.nodes)} not matching"
        f"number of buses {len(dist_model.buses)}"
        raise ValueError(msg)
