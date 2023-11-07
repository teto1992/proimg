import sys
import json
import argparse
import networkx as nx
import numpy as np
import time 
import random
import math
import json
from swiplserver import PrologMQI, PrologThread

class PrologServer:
    # Initialises a new instance of the PrologServer class.
    # If programs is not empty, loads the programs into the Prolog server.
    # If datafiles is not empty, consults the datafiles into the Prolog server.
    def __init__(self, programs = [], datafiles = []):
        self.mqi = PrologMQI()
        self.thread = self.mqi.create_thread()
        for program in programs:
            self.load_program(program)
        for datafile in datafiles:
            self.consult(datafile)

    # Loads a program into the Prolog server through the [filename] predicate.
    def load_program(self, filename: str):
        return self.thread.query("[{}]".format(filename))

    # Consults a datafile into the Prolog server through the loadFile predicate.
    # Hack: loadFile implements a read&assert loop, faster than built-in consult. 
    # It retracts all predicates specified in the to_retract string.
    def consult(self, filename: str, to_retract: str = None):
        if to_retract is None:
            self.thread.query("loadFile('{}', [])".format(filename))
        else:
            self.thread.query("loadFile('{}',{})".format(filename, to_retract))
    
    # Returns the first result of the specified query within the specified timeout.
    def query(self, query: str, timeout=60):
        # throws exception at timeout
        result = self.thread.query("once({})".format(query), query_timeout_seconds=timeout)
        return result

    # Stops the Prolog server.
    def stop(self):
        self.mqi.stop()


def write_to_file(G, filename):

    f = open(filename,"w")

    f.write('maxReplicas('+str(6)+').\n')

    for i in range(0,G.number_of_nodes()):
        if G.nodes[i]['on']:
            node = G.nodes[i]
            newnode = 'node(n'+str(i)+','+str(node['storage'])+','+str(node['cost'])+').\n'
            f.write(newnode)
    
    for (i,j) in G.edges():
        link=G.edges[i,j]
        newlink='link(n'+str(i)+',n'+str(j)+','+str(link['latency'])+','+str(link['bandwidth'])+').\n'
        f.write(newlink)
        newlink='link(n'+str(j)+',n'+str(i)+','+str(link['latency'])+','+str(link['bandwidth'])+').\n'
        f.write(newlink)
    
    f.close()

def path_bandwidth(G,path):
    min_bandwidth = math.inf
    for i in range(0,len(path)-1):
        bandwidth = G.edges[path[i],path[i+1]]['bandwidth']
        if (bandwidth < min_bandwidth):
            min_bandwidth = bandwidth
    return min_bandwidth

def routing(G):
    paths = dict(nx.all_pairs_dijkstra(G, weight='latency'))

    # complete topology with routing latency and bandwidth
    for i in range(0,G.number_of_nodes()):
        for j in range(0,G.number_of_nodes()):
            if not ((i,j) in G.edges()):
                G.add_edge(i,j)
                latency = paths[i][0][j]
                bandwidth = path_bandwidth(G,paths[i][1][j])
                G.edges[i,j]['latency'] = latency
                G.edges[i,j]['bandwidth'] = bandwidth
                G.edges[i,j]['physical'] = False

    return G

def generate_infrastructure_barabasi_albert(number_of_nodes, m):

    G = nx.generators.random_graphs.barabasi_albert_graph(number_of_nodes,m,seed=481183) # random_internet_as_graph(number_of_nodes) # 

    for i in range(0,number_of_nodes):
        edge = random.random() > 0.2 # 80% of the nodes in the edge, 20% in the cloud

        if (edge):
            G.nodes[i]['edge'] = True
            G.nodes[i]['storage'] = random.choice([8,16,32])
        else:
            G.nodes[i]['edge'] = False
            G.nodes[i]['storage'] = random.choice([64,128,256,512])
        
        G.nodes[i]['on'] = True
        G.nodes[i]['cost'] = str(random.randint(1,10))

    for (i,j) in G.edges():
        G.edges[i,j]['latency'] = int(random.randint(1,20))#,25,50,100,150]))
        G.edges[i,j]['bandwidth'] = int(random.randint(5,500))# , 50, 100, 200, 500, 1000]))
        G.edges[i,j]['physical'] = True

    G = routing(G)

    return G

def changeInfra(G):

    # node crashes
    for i in range(0,G.number_of_nodes()):
        if G.nodes[i]['edge']:
            G.nodes[i]['on'] = random.random() > 0.1
        else:
            G.nodes[i]['on'] = random.random() > 0.01
        
    for (i,j) in G.edges():
        # link variations
        if G.edges[i,j]['physical']:
            # link degradation
            if random.random() > 0.5:
                change = random.uniform(0.05,0.25)
                G.edges[i,j]['latency'] += int(change * G.edges[i,j]['latency'])
                G.edges[i,j]['bandwidth'] -= int(change * G.edges[i,j]['bandwidth'])
            # link improvement
            else:
                change = random.uniform(0.05,0.25)
                G.edges[i,j]['latency'] -= int(change * G.edges[i,j]['latency'])
                G.edges[i,j]['bandwidth'] += int(change * G.edges[i,j]['bandwidth'])
        else: # virtual link
            G.remove_edge(i,j)

    # complete topology with routing latency and bandwidth
    G = routing(G)

    write_to_file(G, "infra.pl")


def simulate(n, m, epochs):

    G = generate_infrastructure_barabasi_albert(n,m)
    write_to_file(G, "infra.pl")

    times = []

    prolog = PrologServer()
    prolog.load_program(['main', 'config'])

    with PrologMQI() as mqi:
        with mqi.create_thread() as prolog_thread:
            for i in range(epochs):
                print("Epoch:"+str(i))
                
                prolog.consult(filename='images.pl', to_retract='[image(_,_,_)]')
                prolog.consult(filename='infra.pl', to_retract='[node(_,_,_), link(_,_,_,_), maxReplicas(_)]')  

                try:
                    result = prolog.query("declace(P, Cost, Time)", 60)
                    times.append(result[0]['Time'])
                    #print(result[0]['KOImages'])
                    print(result[0]['Cost'])
                    print(result[0]['P'])
                    print("time:"+ str(result[0]['Time']))   
                    changeInfra(G)
                    write_to_file(G, "infra.pl") 
                except:
                    G = generate_infrastructure_barabasi_albert(n,m)
                    write_to_file(G, "infra.pl")
                    print("timeout exceeded")
                    continue

            
    prolog.stop()

    print(sum(times)/len(times))
                    

simulate(1024,3,10)

