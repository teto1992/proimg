import sys
import json
from argparse import ArgumentParser

import networkx as nx
import numpy as np


def node_atom(i, storage, cost):
    return "node(n{}, {}, {}).".format(i, storage, cost)


def link_atom(i, j, latency, bandwidth):
    return "link(n{}, n{}, {}, {}).".format(i, j, latency, bandwidth)


def write(string, target):
    # https://stackoverflow.com/questions/17602878/how-to-handle-both-with-open-and-sys-stdout-nicely
    sys.stdout.close = lambda: None
    with (open(target, "w") if target else sys.stdout) as hnd:
        hnd.write(string)

def generate_infrastructure(n, m, seed, params):
    rnd = np.random.default_rng(seed)

    G = nx.generators.random_graphs.barabasi_albert_graph(n, m, seed)

    for i in range(n): 
        is_edge_node = rnd.random() > params['network']['edge-cloud-ratio'] 

        if is_edge_node:
            G.nodes[i]["storage"] = rnd.choice(params['node']['edge-storage'])
        else:
            G.nodes[i]["storage"] = rnd.choice(params['node']['cloud-storage'])

        G.nodes[i]["cost"] = rnd.choice(params['node']['unit-cost'])

    for (i, j) in G.edges():
        G.edges[i, j]["latency"] = rnd.choice(params['link']['latency'])
        G.edges[i, j]["bandwidth"] = rnd.choice(params['link']['bandwidth'])

    return G

def reify_infrastructure(G):
    prg = [":-dynamic node/4."]
    for i, attr in G.nodes.items():
        prg.append(node_atom(i, attr["storage"], attr["cost"]))
    for (i, j), attr in G.edges.items():
        prg.append(link_atom(i, j, attr["latency"], attr["bandwidth"]))

    return "\n".join(prg)

def parse_args():
    p = ArgumentParser()
    p.add_argument('num_nodes', type=int, help="Number of nodes in the generated network.")
    p.add_argument('num_edges', type=int, help="Number of edges under AB generation scheme.")
    p.add_argument('-o', '--output-file', type=str, help="Output file.")
    p.add_argument('-s', '--seed', type=int, default=481183, help="Numpy seed for random number generation.")
    p.add_argument('-p', '--params', type=str, default=None, help="JSON containing node, link properties ranges.")
    args = p.parse_args()
    return args

def load_params(filename):
    DEFAULT_PARAMETERS = {
        "network": {
            "edge-cloud-ratio": 0.2,
        },
        "node": {
            "edge-storage": [2, 4, 8, 16, 32],
            "cloud-storage": [64, 128, 256],
            "unit-cost": [1, 2, 3, 4, 5],
        },
        "link": {
             "latency": [5, 10, 25, 50, 100, 150],
             "bandwidth": [10, 20, 50, 100, 200, 500, 1000],
        },
    }

    if filename is None:
        return DEFAULT_PARAMETERS

    with open(filename) as f:
        return json.load(f)

if __name__ == '__main__':
    args = parse_args()
    params = load_params(args.params)

    g = generate_infrastructure(args.num_nodes, args.num_edges, args.seed, params)
    prg = reify_infrastructure(g)

    write(prg, args.output_file)
