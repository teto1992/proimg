from abc import ABC
import networkx as nx


"""
A set of classes that wraps networkx.generators.*_graph classes.
"""


class GraphGenerator(ABC):
    def __init__(self, nx_generator, **kwargs):
        self.kwargs = kwargs
        self.generator = nx_generator

    def generate(self, random_state) -> nx.Graph:
        return self.generator(seed=random_state, **self.kwargs)


class BarabasiAlbert(GraphGenerator):
    def __init__(self, **kwargs):
        assert "n" in kwargs
        assert "m" in kwargs
        assert "seed" not in kwargs
        super().__init__(nx.generators.barabasi_albert_graph, **kwargs)


class ErdosRenyi(GraphGenerator):
    def __init__(self, **kwargs):
        assert "n" in kwargs
        assert "p" in kwargs
        assert "seed" not in kwargs
        super().__init__(nx.generators.erdos_renyi_graph, **kwargs)
