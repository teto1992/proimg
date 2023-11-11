import sys
import time
from typing import List, Tuple

from numpy.random import RandomState

from declace.api.prolog import PrologQuery
from declace.exceptions import UnsatisfiableContinuousReasoning, UnsatisfiablePlacement
from declace.model import Problem, PRECISION
from declace.reasoners.cr.prolog_cr import PrologContinuousReasoningService
from declace.reasoners.opt.asp_opt import ASPOptimalReasoningService
from declace.reasoners.opt.prolog_heu import PrologHeuristicReasoningService

from declace_simulation_framework.simulator.saboteurs import InstanceSaboteur
from declace_simulation_framework.utils.network_utils import (
    prune_network,
    snapshot_closure,
)

from loguru import logger

LOG_LEVEL_NAME = "PAPER_SIMULATOR"
logger.level(LOG_LEVEL_NAME, no=15, color="<blue>")


class Stopwatch:
    class Trigger:
        def __init__(self, stopwatch, tag):
            self.tag = tag
            self.stopwatch = stopwatch

        def __enter__(self):
            self.start = time.time()

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.stop = time.time()
            self.stopwatch.data[self.tag] = self.stop - self.start

    def __init__(self):
        self.data = {}

    def trigger(self, tag):
        return Stopwatch.Trigger(self, tag)

    def get(self, tag):
        return self.data[tag]

    def clear(self):
        self.data = {}


class PaperBenchmarkSimulator:
    def __init__(
        self,
        problem: Problem,
        saboteur: InstanceSaboteur,
        shutdown_probability: float,
        cr_timeout: int,
        opt_timeout: int,
        random_state: RandomState
    ):

        self.original_problem = problem
        self.saboteur = saboteur
        self.shutdown_probability = shutdown_probability

        self.asp_scratch = ASPOptimalReasoningService(PRECISION)
        self.prolog_cr = PrologContinuousReasoningService()
        self.prolog_scratch = PrologHeuristicReasoningService()

        self.cr_timeout = cr_timeout
        self.opt_timeout = opt_timeout

        self.random_state = random_state

    def __cleanup__(self):
        self.prolog_scratch.cleanup()
        self.prolog_cr.cleanup()

    def ruin(self):
        pruned_network = prune_network(self.original_problem.network, self.shutdown_probability, self.random_state)
        closure = snapshot_closure(pruned_network)
        current_problem = self.original_problem.change_underlying_network(closure)
        return current_problem

    def simulate(self, n):
        stopwatch = Stopwatch()

        problem = self.ruin()

        with stopwatch.trigger('asp'):
            asp_placement, asp_stats = self.asp_scratch.opt_solve(problem, self.opt_timeout)
        self.prolog_cr.inject_placement(asp_placement)

        with stopwatch.trigger('heu'):
            heu_placement, heu_stats = self.prolog_scratch.opt_solve(problem, self.opt_timeout)

        print(stopwatch.data)

        for step in range(1, n):
            problem = self.ruin()
            stopwatch.clear()

            with stopwatch.trigger('asp'):
                asp_placement, asp_stats = self.asp_scratch.opt_solve(problem, self.opt_timeout)

            with stopwatch.trigger('heu'):
                self.prolog_scratch.prolog_server.thread.query("retractall(placedImages(_,_,_))")
                heu_placement, heu_stats = self.prolog_scratch.opt_solve(problem, self.opt_timeout)

            with stopwatch.trigger('cr'):
                cr_placement, cr_stats = self.prolog_cr.cr_solve(problem, self.cr_timeout)

            print(stopwatch.data)

        self.__cleanup__()
