import sys
import json
import argparse
import networkx as nx
import numpy as np
import random

# A container image is a triple ⟨i, s, m⟩ where i de-
# notes the unique image identifier, s the size of the image in
# Megabytes (MB), and m the maximum amount of time in mil-
# liseconds tolerated to download such image onto a target node

images_string = '''
max_replicas(alpine, 50).
max_replicas(ngnix,  50).
max_replicas(busybox,50).
max_replicas(ubuntu, 50).
max_replicas(python, 50).

image(alpine,3,300).
image(ngnix,65,300).
image(busybox,2,300).
image(ubuntu,28,300).
image(python,46,300).

'''


def generate_infrastructure_barabasi_albert(
    random_seeds : 'list[int]',
    init_size_network : int,
    end_size_network : int,
    step_size_network : int) -> None:
    
    fp = open(f"images.lp","w")
    fp.write(images_string)
    fp.close()
    # from the GNOSIS paper
    m_list = [1,3]
    for number_of_nodes in range(init_size_network,end_size_network+1,step_size_network):
        print(f"Generating networks for size {number_of_nodes}")
        for current_m in m_list:
            for seed in random_seeds:
                G = nx.generators.random_graphs.barabasi_albert_graph(number_of_nodes,current_m,seed=seed)
                #G = nx.generators.complete_graph(number_of_nodes)

                for i in range(0,number_of_nodes):
                    edge = random.random() > 0.2 # 80% of the nodes in the edge, 20% in the cloud

                    if (edge):
                        # G.nodes[i]['storage'] = str(random.choice([2,4,8,16,32]))
                        G.nodes[i]['storage'] = str(1000)
                    else:
                        # G.nodes[i]['storage'] = str(random.choice([64,128,256]))
                        G.nodes[i]['storage'] = str(1000)
                    
                    G.nodes[i]['cost'] = str(random.choice([1,2,3,4,5]))

                for (i,j) in G.edges():
                    G.edges[i,j]['latency'] = int(random.choice([5,10]))#,25,50,100,150]))
                    G.edges[i,j]['bandwidth'] = int(random.choice([1000, 2000]))# , 50, 100, 200, 500, 1000]))

                paths = dict(nx.all_pairs_dijkstra(G, weight='latency'))


                f = open(f"{number_of_nodes}/b_a_{number_of_nodes}_{current_m}_{seed}.pl","w+")

                for i in range(0,number_of_nodes):
                    node = G.nodes[i]
                    newnode = 'node(n'+str(i)+','+node['storage']+','+node['cost']+').\n'
                    f.write(newnode)
                for (i,j) in G.edges():
                    link=G.edges[i,j]
                    newlink='link(n'+str(i)+',n'+str(j)+','+str(link['latency'])+','+str(link['bandwidth'])+').\n'
                    f.write(newlink)
                    newlink='link(n'+str(j)+',n'+str(i)+','+str(link['latency'])+','+str(link['bandwidth'])+').\n'
                    f.write(newlink)

                for i in range(0,number_of_nodes):
                    for j in range(0,number_of_nodes):
                        if not ((i,j) in G.edges()):
                            latency = paths[i][0][j]
                            bandwidth = path_bandwidth(G,paths[i][1][j])
                            newlink='link(n'+str(i)+',n'+str(j)+','+str(latency)+','+str(bandwidth)+').\n'
                            f.write(newlink)
                            newlink='link(n'+str(j)+',n'+str(i)+','+str(latency)+','+str(bandwidth)+').\n'
                            f.write(newlink)

                f.close()

def path_bandwidth(G,path):
    min_bandwidth = 1000
    for i in range(0,len(path)-1):
        bandwidth = G.edges[path[i],path[i+1]]['bandwidth']
        if (bandwidth < min_bandwidth):
            min_bandwidth = bandwidth
    return min_bandwidth

p = argparse.ArgumentParser()
p.add_argument("min_nodes", type=int, default=25)
p.add_argument("max_nodes", type=int, default=1000)
p.add_argument("step_nodes", type=int, default=25)
# 0 -> barabasi albert
# 1 -> Erdos-Renyi
# 2 -> Watts-Strogatz
p.add_argument("structure", type=int, default=0)

args = p.parse_args()

random_seeds : 'list[int]' = list(range(0,10))

generate_infrastructure_barabasi_albert(
    random_seeds,
    args.min_nodes,
    args.max_nodes,
    args.step_nodes
)
