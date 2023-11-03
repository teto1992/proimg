from typing import Tuple

from swiplserver import PrologMQI, PrologThread
from dataclasses import dataclass


@dataclass(frozen=True)
class PrologQuery:
    predicate_name: str
    vars: Tuple[str, ...]

    def __str__(self):
        return "{}({})".format(self.predicate_name, ",".join(self.vars))



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

"""
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
                    

simulate(100,3,10)
"""

