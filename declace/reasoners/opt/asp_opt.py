import logging
import time
from collections import defaultdict
from math import ceil
from pathlib import Path
from typing import List, Tuple

import clingo

from declace.exceptions import UnsatisfiablePlacement
from declace.model import Problem, Placement, Image
from declace.reasoners import OIPPReasoningService


class Messages:
    TRANSFER_TIME_COMPUTATION = (
        "Computing @-term: compute_transfer_time({},{},{}) = {} ~ {}"
    )
    INTERMEDIATE_SOLUTION = "Found a solution with cost {}, optimal? {}, model: \n{}"


class Context:
    def __init__(self, debug=False, precision=3):
        # TODO: Unità di misura, cifre aritmetica
        self.precision = precision
        self.debug = debug

    def compute_transfer_time(self, size, bandwidth, latency):
        # latency.number / 1000 ms -> s
        r_seconds = (
            float(size.number) * float(8.0) / float(bandwidth.number)
            + float(latency.number) / 10**self.precision
        )
        r_milliseconds = r_seconds * 10**self.precision

        if self.debug:
            logging.debug(
                Messages.TRANSFER_TIME_COMPUTATION.format(
                    size, bandwidth, latency, r_milliseconds, ceil(r_milliseconds)
                )
            )

        return clingo.Number(int(ceil(r_milliseconds)))


def project_answer_set(model):
    return [sym for sym in model.symbols(shown=True) if sym.match("placement", 2)]


class SolutionCallback:
    def __init__(self, debug=True):
        self._placement = None
        self._cost = None
        self._optimal = False

        self.debug = debug
        self.init_time = time.time()
        self.intermediate_solutions: List[Tuple[int, float]] = []

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
        assert model.optimality_proven
        self._placement = atoms
        self._cost = model.cost
        self._optimal = True
        exec_time = time.time() - self.init_time
        print(f"OPTIMAL Cost: {model.cost[0]} computed in: {exec_time:.3f} seconds")
        self.intermediate_solutions.append((model.cost[0], exec_time))
        return False

    @property
    def best_known_placement(self):
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


class ASPOptimalReasoningService(OIPPReasoningService):
    SOURCE_FOLDER = Path(__file__).parent / 'asp_opt_source'


    def cleanup(self):
        pass

    def __init__(self):
        # cost_at_time[i] = (a, b) -> i-th candidate model has cost a, found at time b
        # TODO: Refactor into a Stats class
        self.cost_at_time: List[Tuple[int, float]] = []

    def opt_solve(self, problem: Problem, timeout: int) -> Placement:
        # Initialize a Clingo
        ctl = clingo.Control(["--models=0", "--opt-mode=optN"])
        ctl.load((ASPOptimalReasoningService.SOURCE_FOLDER / 'encoding.lp').as_posix())  # encoding

        # Serialize problem into a set of facts
        ctl.add("base", [], problem.as_facts)

        # Grounding
        ctl.ground([("base", [])], context=Context(debug=True))
        print("GROUND?")

        # Solving
        cb = SolutionCallback(True)
        with ctl.solve(async_=True, on_model=cb, on_core=lambda x: print("CORE", x), on_unsat=lambda x: print("UNSAT,", x)) as handle:
            start = time.time()
            handle.wait(timeout)
            print("End search!", time.time() - start)
            ans = handle.get()

            if ans.unsatisfiable:
                raise UnsatisfiablePlacement()

            elif ans.unknown:
                raise RuntimeError("Something was wrong in the clingo call, timeout?")

        # Parse the answer back into a Placement
        return cb.best_known_placement
