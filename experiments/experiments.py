import sys
import json
from argparse import ArgumentParser

import networkx as nx
import numpy as np


def node_atom(i, storage, cost):
    """
    Encodes a network's node as a node/3 atom.
    """
    return "node(n{}, {}, {}).".format(i, storage, cost)


def link_atom(i, j, latency, bandwidth):
    """
    Encodes a network's link as a link/4 atom.
    """
    return "link(n{}, n{}, {}, {}).".format(i, j, latency, bandwidth)


def write(string, target):
    # https://stackoverflow.com/questions/17602878/how-to-handle-both-with-open-and-sys-stdout-nicely
    sys.stdout.close = lambda: None
    with (open(target, "w") if target else sys.stdout) as hnd:
        hnd.write(string)


def generate_infrastructure(n, m, seed, params):
    """
    Generates a network topology according to experiment's parameters:
      - network/edge-cloud-ratio: probabilty a node is assigned to edge of the network
      - node/{edge,cloud}-storage: storage available in the node (MB)
      - node/cost: unit-cost for transferring a MB from that node
      - link/latency: latency on a given network's link
      - link/bandwidth: bandwidth on a given network's link
    """

    rnd = np.random.default_rng(seed)

    G = nx.generators.random_graphs.barabasi_albert_graph(n, m, seed)

    for i in range(n):
        is_edge_node = rnd.random() > params["network"]["edge-cloud-ratio"]

        if is_edge_node:
            G.nodes[i]["storage"] = rnd.choice(params["node"]["edge-storage"])
        else:
            G.nodes[i]["storage"] = rnd.choice(params["node"]["cloud-storage"])

        G.nodes[i]["cost"] = rnd.choice(params["node"]["unit-cost"])

    for (i,j) in G.edges():
        G.edges[i,j]['latency'] = str(rnd.choice([5,10,25,50,100,150]))
        G.edges[i,j]['bandwidth'] = str(rnd.choice([10, 20, 50, 100, 200, 500, 1000]))

    f = open("infra.pl","w+")
    f.write(':-dynamic node/4.\n')
    for i in range(0,n):
        node = G.nodes[i]
        newnode = 'node(n'+str(i)+','+node['storage']+','+node['cost']+').\n'
        f.write(newnode)
    for (i,j) in G.edges():
        link=G.edges[i,j]
        newlink='link(n'+str(i)+',n'+str(j)+','+str(link['latency'])+','+link['bandwidth']+').\n'
        f.write(newlink)

    f.close()

generateInfrastructure(481183, 100, 3)
