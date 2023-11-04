"""
A Network object models a (simplified) network topology, ...
"""
import networkx as nx
from numpy.random import RandomState
import itertools
from declace.model import *


def prune_network(
    network: NetworkSnapshot, shut_down_probability: float, random_state: RandomState
) -> NetworkSnapshot:
    """
    Kills some nodes within the network and corresponding links.
    """

    alive_nodes = [
        node for node in network.nodes if random_state.random() > shut_down_probability
    ]
    alive_node_ids = set(x.id for x in alive_nodes)
    alive_links = [
        link
        for link in network.links
        if link.source in alive_node_ids and link.target in alive_node_ids
    ]
    return NetworkSnapshot(alive_nodes, alive_links)


def as_nx_graph(network: NetworkSnapshot) -> nx.Graph:
    """
    Maps a NetworkSnapshot into a nx.Graph, preserving atttributes on links and nodes.
    """

    graph = nx.Graph()
    for node in network.nodes:
        graph.add_node(node.id, storage=node.storage, cost=node.cost)

    for link in network.links:
        graph.add_edge(
            link.source, link.target, latency=link.latency, bandwidth=link.bandwidth
        )

    return graph


def snapshot_closure(network: NetworkSnapshot) -> NetworkSnapshot:
    """
    Computes transitive closure of the network, introducing virtual edges and assigning them the worst-possible latency and bandwidth.
    """

    graph = as_nx_graph(network)
    node_ids = [int(x) for x in graph.nodes]
    all_edges = itertools.combinations(node_ids, 2)
    virtual_edges = [e for e in all_edges if e not in graph.edges]

    for i, j in virtual_edges:
        graph.add_edge(i, j, latency=math.inf, bandwidth=math.inf)

    # a volte il grafo non è connesso quindi in fare paths[i][0][j] sotto scoppia
    # li aggiungo prima con lat, band infinita tanto dijkstra fa shortest path su latency
    # e fa min di bandwidth
    paths = dict(nx.all_pairs_dijkstra(graph, weight="latency"))

    def virtual_link(i, j):
        # Sum of latencies
        latency = paths[i][0][j]

        # Bandwidths along the shortest path i--j
        path = paths[i][1][j]
        bandwidths_along_path = [
            graph.edges[path[x], path[x + 1]]["bandwidth"] for x in range(len(path) - 1)
        ]

        # The virtual link has the sum of latencies & minimum bandwidth
        link = Link(i, j, latency, min(bandwidths_along_path))

        return link

    return NetworkSnapshot(
        network.nodes,
        list(network.links) + [virtual_link(i, j) for i, j in virtual_edges],
    )
