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
    def __init__(self):
        self.elapsed = None

    def start(self):
        assert self.elapsed is None
        self.elapsed = time.time()

    def stop(self):
        val = time.time() - self.elapsed
        self.elapsed = None
        return val

class PaperBenchmarkSimulator:
    def __init__(
        self,
        problem: Problem,
        saboteur: InstanceSaboteur,
        shutdown_probability: float,
        cr_timeout: int,
        opt_timeout: int,
    ):

        self.original_problem = problem
        self.saboteur = saboteur
        self.shutdown_probability = shutdown_probability

        self.asp_scratch = ASPOptimalReasoningService(PRECISION)
        self.prolog_cr = PrologContinuousReasoningService()
        self.prolog_scratch = PrologHeuristicReasoningService()

        self.cr_timeout = cr_timeout
        self.opt_timeout = opt_timeout

    def __cleanup__(self):
        # ...
        pass

    def ruin(self, random_state: RandomState):
        pruned_network = prune_network(self.original_problem.network, self.shutdown_probability, random_state) #self.original_problem.network #
        closure = snapshot_closure(pruned_network)
        current_problem = self.original_problem.change_underlying_network(closure)
        return current_problem

    def simulate(self, n, random_state):
        stopwatch = Stopwatch()
        ASP_SCRATCH_TIMES: List[Tuple[float, int]] = []
        PROLOG_SCRATCH_TIMES: List[Tuple[float, int]] = []
        DECLACE_TIMES: List[Tuple[float, int]] = []

        ##### FIRST SOLVING SHOT

        stopwatch.start()
        problem = self.ruin(random_state)
        print("EPOCH 0 RUINING INFRASTRUCTURE ELAPSED {:.3f}s".format(stopwatch.stop()))

        stopwatch.start()
        placement, stats = self.asp_scratch.opt_solve(problem, self.opt_timeout)
        print("EPOCH 0 ASP OPT SOLVING ELAPSED {:.3f}s".format(stopwatch.stop()))

        print("="*10, placement, "="*10)

        ASP_SCRATCH_TIMES.append(
            (float(stats['time']), int(placement.cost))
        )

        DECLACE_TIMES.append(
            (float(stats['time']), int(placement.cost))
        )
        self.prolog_cr.inject_placement(placement)

        stopwatch.start()
        placement, stats = self.prolog_scratch.opt_solve(problem, self.opt_timeout)
        PROLOG_SCRATCH_TIMES.append(
            (float(stats['time']), int(placement.cost))
        )
        print("EPOCH 0 PROLOG HEU SOLVING ELAPSED {:.3f}s".format(stopwatch.stop()))
        print("="*10, placement, "="*10)


        #####

        for step in range(1, n):
            # ho scassato la rete
            stopwatch.start()
            problem = self.ruin(random_state)
            print("EPOCH {} INFRASTRUCTURE RUIN ELAPSED {:.3f}s".format(step, stopwatch.stop()))

            # prendo il tempo con ASP ottimo
            stopwatch.start()
            asp_placement, asp_stats = self.asp_scratch.opt_solve(problem, self.opt_timeout)
            ASP_SCRATCH_TIMES.append(
                (float(stats['time']), int(asp_placement.cost))
            )
            print("EPOCH {} ASP OPT SOLVING ELAPSED {:.3f}s:{}".format(step, stopwatch.stop(), asp_placement.cost))
            print("=" * 10, asp_placement, "=" * 10)

            self.prolog_scratch.prolog_server.thread.query("retractall(placedImages(_,_,_))")

            # prendo il tempo con prolog heuristico
            stopwatch.start()
            placement, stats = self.prolog_scratch.opt_solve(problem, self.opt_timeout)
            PROLOG_SCRATCH_TIMES.append(
                (float(stats['time']), int(placement.cost))
            )
            print("EPOCH {} PROLOG HEU SOLVING ELAPSED {:.3f}s:{}".format(step, stopwatch.stop(), placement.cost))
            print("=" * 10, placement, "=" * 10)
            
            if placement.cost < asp_placement.cost:
                print(f"Cost error: ASP: {asp_placement.cost}, prolog heu: {placement.cost}")
            #     print("asp_placement: ")
            #     print(asp_placement)
            #     print("heu")
            #     print(placement)
            #     print("instance")
                print(problem.as_facts)
            #     return -1, -1, -1
            
            mask = "GREPME EPOCH {} [time:cost]: {:.3f}s:{} {:.3f}s:{}"

            print(mask.format(
                step, *ASP_SCRATCH_TIMES[-1], *PROLOG_SCRATCH_TIMES[-1])
            )

        # oppure un csv
        # <nome_simulazione>.csv
        # step,asp_opt_time,asp_opt_cost,prolog_heu_time,prolog_heu_cost,declace_time,declace_cost
        return ASP_SCRATCH_TIMES, PROLOG_SCRATCH_TIMES, DECLACE_TIMES