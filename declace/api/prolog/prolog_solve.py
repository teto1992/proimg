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
    def __init__(self, programs = [], datafiles = []):
        self.mqi = PrologMQI()
        self.thread = self.mqi.create_thread()
        for program in programs:
            self.load_program(program)
        for datafile in datafiles:
            self.consult(datafile)

    def load_program(self, filename: str):
        self.thread.query("[{}]".format(filename))

    def consult(self, filename: str, to_retract: str = None):
        if to_retract is None:
            self.thread.query("loadFile('{}', [])".format(filename))
        else:
            self.thread.query("loadFile('{}','{}')".format(filename, to_retract))

    def query(self, query: str, timeout=60):
        # throws exception at timeout
        self.thread.query("once({})".format(query), query_timeout_seconds=timeout)

    def stop(self):
        self.mqi.stop()



# [ images, infrastrture ]
# node/3 -> node(_,_,_)
#solve_prolog(['main_cr.pl', 'config.pl'], [('infrastructure.pl', ['node/3', 'link/4']), ('images.pl', [...]), 'declace(P,Cost,Time)')



