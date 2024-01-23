""" This module contains class to create networkx from distribution model."""
import networkx as nx

from gdm.distribution.distribution_model import DistributionModel


class DistributionGraph:
    def __init__(self, distribution_model: DistributionModel):
        """constructor for the distribution graph module.

        Args:
            distribution_model (DistributionModel): instance of the distribution model
        """

        self.dist_model = distribution_model
        self.graph_model = nx.Graph()
        self._parse_buses()
        self._parse_branches()
        self._parse_transformers()

    @property
    def graph(self):
        """Method to return graph instance."""
        return self.graph_model

    def _parse_buses(self):
        """Method parses the bus models."""
        for bus in self.dist_model.buses:
            self.graph_model.add_node(
                bus.name,
                model=bus,
                loads=list(filter(lambda x: x.bus.name == bus.name, self.dist_model.loads)),
                capacitors=list(
                    filter(lambda x: x.bus.name == bus.name, self.dist_model.capacitors)
                ),
                voltage_sources=list(
                    filter(lambda x: x.bus.name == bus.name, self.dist_model.voltage_sources)
                ),
            )

    def _parse_branches(self):
        """Method parses the brach models."""
        models = [
            self.dist_model.ac_lines,
            self.dist_model.switches,
            self.dist_model.fuses,
            self.dist_model.sectionalizers,
            self.dist_model.breakers,
        ]

        for model in models:
            for line in model:
                self.graph_model.add_edge(line.from_bus.name, line.to_bus.name, model=line)

    def _parse_transformers(self):
        """Method parses the transformer models."""
        for transformer in self.dist_model.transformers:
            windings = {wdg.sequence_number: wdg for wdg in transformer.windings}
            for coupling in transformer.wdg_couplings:
                from_winding = windings[coupling.from_wdg_seq_num]
                to_winging = windings[coupling.to_wdg_seq_num]
                self.graph_model.add_edge(
                    from_winding.bus.name,
                    to_winging.bus.name,
                    from_winding_id=coupling.from_wdg_seq_num,
                    to_winding_id=coupling.to_wdg_seq_num,
                    model=transformer,
                )
