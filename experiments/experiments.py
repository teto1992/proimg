import networkx as nx
import numpy as np
import math
from pyswip import Prolog
import time
import re

def generateInfrastructure(seed, n, m):
    rnd = np.random.default_rng(seed)
        
    G = nx.generators.random_graphs.barabasi_albert_graph(n,m,seed)

    for i in range(0,n):
        edge = rnd.random() > 0.2 # 80% of the nodes in the edge, 20% in the cloud

        if (edge):
            G.nodes[i]['storage'] = str(rnd.choice([2,4,8,16,32]))
        else:
            G.nodes[i]['storage'] = str(rnd.choice([64,128,256]))
        
        G.nodes[i]['cost'] = str(rnd.choice([1,2,3,4,5]))

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

generateInfrastructure(481183, 10, 3)
