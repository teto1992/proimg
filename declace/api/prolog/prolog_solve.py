from typing import Tuple

from swiplserver import PrologMQI
from dataclasses import dataclass


@dataclass(frozen=True)
class PrologQuery:
    predicate_name: str
    vars: Tuple[str, ...]

    def __str__(self):
        return "{}({})".format(self.predicate_name, ",".join(self.vars))



class PrologServer:
    def __init__(self):
        self.mqi = PrologMQI()
        self.thread = self.mqi.create_thread()

    def load_program(self, filename: str):
        self.thread.query("[{}]".format(filename))

    def query(self, query: str):
        self.thread.query("once({})".format(query))



# [ images, infrastrture ]
# node/3 -> node(_,_,_)
solve_prolog(['main_cr.pl', 'config.pl'], [('infrastructure.pl', ['node/3', 'link/4']), ('images.pl', [...]), 'declace(P,Cost,Time)')




def solve_prolog(programs, data, query, timeout=60):
    # TODO: Non ho capito un cazzo
    # Vorrei usarlo così:
    # solve_prolog('prog.lp', PrologQuery('declace',('P','Time','Cost')))

    server = PrologServer()
    for program in programs:
        server.load_program(program)

    for datum in data:
        server.query(datum)



    with PrologMQI() as mqi:
        with mqi.create_thread() as prolog_thread:
                print("Epoch:"+str(i))
                if (i == 0):
                    prolog_thread.query("[main],once(loadInfrastructure())")
                else:
                    prolog_thread.query("once(loadInfrastructure())")

                # TODO: handle timeout and false

                try:
                    result = prolog_thread.query("declace(P, Cost, Time)",query_timeout_seconds = 60)
                    times.append(result[0]['Time'])
                    #print(result[0]['KOImages'])
                    print(result[0]['Cost'])
                    # print(result[0]['NewPlacement'])
                    print("time:"+ str(result[0]['Time']))
                    changeInfra(G)
                    write_to_file(G, "infra.pl")
                except:
                    G = generate_infrastructure_barabasi_albert(n,m)
                    write_to_file(G, "infra.pl")
                    print("timeout exceeded")
                    continue