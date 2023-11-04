from pathlib import Path
from typing import Tuple, List, Optional

from swiplserver import PrologMQI, PrologThread
from dataclasses import dataclass


@dataclass(frozen=True)
class PrologQuery:
    predicate_name: str
    varnames: List[str]

    @property
    def as_atom(self):
        return "{}({})".format(self.predicate_name, ", ".join(self.varnames))

    @staticmethod
    def from_string(pname, vars):
        return PrologQuery(pname, vars.split(","))


@dataclass(frozen=True)
class PrologPredicate:
    predicate_name: str
    arity: int

    @staticmethod
    def from_string(string):
        pname, arity = string.split("/")
        return PrologPredicate(pname, int(arity))

    @staticmethod
    def from_strings(*strings: str):
        return [PrologPredicate.from_string(s) for s in strings]


@dataclass(frozen=True)
class PrologDatafile:
    path: Path
    retractions: List[PrologPredicate]

    @property
    def retract_signature(self):
        def retract_atom(predicate: PrologPredicate):
            return "{}({})".format(
                predicate.predicate_name, ",".join("_" for _ in range(predicate.arity))
            )

        return "[{}]".format(", ".join(retract_atom(p) for p in self.retractions))


# TODO: Prints are devs best friends, but maybe we want a logger.


class PrologServer:
    def __init__(self, *programs: Path, verbose=False):
        self.mqi = PrologMQI()
        self.programs = programs
        self.thread: Optional[PrologThread] = None
        self.verbose = verbose

    @property
    def alive(self):
        return self.thread is not None

    def __init_thread__(self):
        self.thread = self.mqi.create_thread()
        if self.verbose:
            print("[VERBOSE] Starting thread: {}".format(str(self.thread)))

    def __load_program__(self, p):
        # TODO: Nicer exceptions
        assert p.exists() and p.is_file()
        q = "['{}']".format(p.as_posix())
        if self.verbose:
            print("[VERBOSE] Loading a program, running query: {}".format(q))
        self.thread.query(q)

    def __load_programs__(self):
        assert self.thread is not None
        for p in self.programs:
            self.__load_program__(p)

    def start(self):
        self.__init_thread__()
        self.__load_programs__()

    def stop(self):
        if self.verbose:
            print("[VERBOSE] Stopping thread & quitting MQI")
        self.thread.stop()
        self.mqi.stop()

    def __enter__(self):
        self.start()

    # Stops the Prolog server.
    def __exit__(self, exc_type, exc_value, exc_tb):
        self.stop()

    # Consults a datafile into the Prolog server through the loadFile predicate.
    # Hack: loadFile implements a read&assert loop, faster than built-in consult.
    # It retracts all predicates specified in the to_retract string.
    def load_datafile(self, datafile: PrologDatafile):
        q = "loadFile('{}', [])".format(
            datafile.path.absolute(), datafile.retract_signature
        )
        if self.verbose:
            print("[VERBOSE] Loading a datafile, running query: {}".format(q))
        self.thread.query(q)

    # def consult(self, filename: str, to_retract: str = None):
    #    if to_retract is None:
    #        self.thread.query("loadFile('{}', [])".format(filename))
    #    else:
    #        self.thread.query("loadFile('{}',{})".format(filename, to_retract))
    # Returns the first result of the specified query within the specified timeout.
    def query(self, query: PrologQuery, timeout=60):
        q = "once({})".format(query.as_atom)
        if self.verbose:
            print(
                "[VERBOSE] Querying for {}".format(query.as_atom),
                "running query: {}".format(q),
            )
        result = self.thread.query(q, query_timeout_seconds=timeout)

        if self.verbose:
            print("[VERBOSE] Results for {}: {}".format(query.as_atom, result))

        return result


if __name__ == "__main__":
    Node, Link, Image, MaxReplicas = PrologPredicate.from_strings(
        "node/3", "link/4", "image/3", "maxReplias/1"
    )

    Declace = PrologQuery.from_string("declace", "P,Cost,Time")

    server = PrologServer(
        Path("/home/antonio/declace/example_prolog_inputs/config.pl"),
        Path("/home/antonio/declace/example_prolog_inputs/main.pl"),
        verbose=True,
    )

    with server:
        infrastructure = Path("/home/antonio/declace/example_prolog_inputs/infra.pl")
        images = Path("/home/antonio/declace/example_prolog_inputs/images.pl")

        server.load_datafile(
            PrologDatafile(infrastructure, retractions=[Node, Link, MaxReplicas])
        )
        server.load_datafile(PrologDatafile(images, retractions=[Image]))

        ans = server.query(Declace, 5)
