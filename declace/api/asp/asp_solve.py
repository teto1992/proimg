import sys
import pathlib
import logging
import time
import clingo
from collections import defaultdict
from math import ceil

from declace.model import Placement, Image

ENCODING = (pathlib.Path(__file__).parent / "encoding.lp").as_posix()

logging.basicConfig(level=logging.DEBUG)


def write(string, target):
    # https://stackoverflow.com/questions/17602878/how-to-handle-both-with-open-and-sys-stdout-nicely
    sys.stdout.close = lambda: None
    with open(target, "w") if target else sys.stdout as hnd:
        hnd.write(string)


class Messages:
    TRANSFER_TIME_COMPUTATION = (
        "Computing @-term: compute_transfer_time({},{},{}) = {} ~ {}"
    )
    INTERMEDIATE_SOLUTION = "Found a solution with cost {}, optimal? {}, model: \n{}"


class Context:
    def __init__(self, debug=False, precision=None):
        self.precision = precision
        self.debug = debug

    def compute_transfer_time(self, size, bandwith, latency):
        # latency.number / 1000 ms -> s
        r_seconds = (
            float(size.number) * float(8.0) / float(bandwith.number)
            + float(latency.number) / 1000.0
        )
        r_milliseconds = r_seconds  # * 1000.0

        if self.debug:
            logging.debug(
                Messages.TRANSFER_TIME_COMPUTATION.format(
                    size, bandwith, latency, r_milliseconds, ceil(r_milliseconds)
                )
            )

        return clingo.Number(int(ceil(r_milliseconds)))


def project_answer_set(model):
    return [sym for sym in model.symbols(shown=True) if sym.match("placement", 2)]


class SolutionCallback:
    def __init__(self, debug=False):
        self._placement = None
        self._cost = None
        self._optimal = False

        self.debug = debug
        self.init_time = time.time()
        self.intermediate_solutions: "list[tuple[int,float]]" = []

    def __call__(self, model):
        atoms = project_answer_set(model)
        if self.debug:
            prg = "\n".join("{}.".format(str(x)) for x in atoms)
            logging.debug(
                Messages.INTERMEDIATE_SOLUTION.format(
                    model.cost, model.optimality_proven, prg
                )
            )

        if not model.optimality_proven:
            exec_time = time.time() - self.init_time
            print(f"Cost: {model.cost[0]} computed in: {exec_time:.3f} seconds")
            self.intermediate_solutions.append((model.cost[0], exec_time))
            # self.current_time = time.time()
            self._placement = atoms
            self._cost = model.cost
            return True

        # self.current_time = time.time()
        self._placement = atoms
        self._cost = model.cost
        self._optimal = True
        exec_time = time.time() - self.init_time
        print(f"OPTIMAL Cost: {model.cost[0]} computed in: {exec_time:.3f} seconds")
        self.intermediate_solutions.append((model.cost[0], exec_time))

        return False

    @property
    def best_known_placement(self):
        # if self._placement is None:
        #    return None

        image_on_nodes = defaultdict(lambda: [])

        for symbol in self._placement:
            image = Image(
                symbol.arguments[0].arguments[0].name,
                symbol.arguments[0].arguments[1].number,
                symbol.arguments[0].arguments[2].number,
            )

            node = symbol.arguments[1].name

            image_on_nodes[node].append(image)

        return Placement(self._cost, image_on_nodes)