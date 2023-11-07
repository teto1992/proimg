import sys
import time

from declace.exceptions import UnsatisfiableContinuousReasoning, UnsatisfiablePlacement
from declace.model import Problem
from declace.reasoners.cr.prolog_cr import PrologContinuousReasoningService
from declace.reasoners.opt.asp_opt import ASPOptimalReasoningService
from declace_simulation_framework.simulator.saboteurs import InstanceSaboteur
from declace_simulation_framework.utils.network_utils import (
    prune_network,
    snapshot_closure,
)


class Simulator:
    def __init__(
            self,
            problem: Problem,
            saboteur: InstanceSaboteur,
            shutdown_probability: float,
            cr_timeout: int,
            opt_timeout: int,
            verbose=True
    ):
        self.original_problem = problem
        self.saboteur = saboteur
        self.shutdown_probability = shutdown_probability

        self.opt = ASPOptimalReasoningService()
        self.cr = PrologContinuousReasoningService(verbose)

        self.cr_timeout = cr_timeout
        self.opt_timeout = opt_timeout

        self.verbose = verbose

    def __cleanup__(self):
        self.cr.cleanup()
        self.opt.cleanup()

    def simulate(self, n, random_state):
        now = time.time()

        preprocessing_time = time.time()
        # Solving OIPP
        pruned_network = prune_network(
            self.original_problem.network, self.shutdown_probability, random_state
        )
        print("Pruning network for first solving shot")

        closure = snapshot_closure(pruned_network)
        print("Computing network closure")
        net_preprocessing_time = time.time() - preprocessing_time

        current_problem = self.original_problem.change_underlying_network(closure)
        current_placement = self.opt.opt_solve(current_problem, self.opt_timeout)
        #

        print("First shot: {:.3f}".format((time.time() - now) - net_preprocessing_time))
        print("Network preprocessing time (routing): {:.3f}s".format(net_preprocessing_time))
        now = time.time()

        current_step = 1
        while current_step < n:
            # Apply saboteurs + Network closure
            preprocessing_time = time.time()
            current_network = prune_network(
                self.original_problem.network, self.shutdown_probability, random_state
            )
            problem = self.saboteur.ruin(
                current_problem.change_underlying_network(current_network), random_state
            )
            current_network = snapshot_closure(problem.network)
            net_preprocessing_time = time.time() - preprocessing_time
            print("Network preprocessing time (routing): {:.3f}s".format(net_preprocessing_time))

            try:
                current_problem = problem.change_underlying_network(current_network)
                current_placement, prolog_solving_time = self.cr.cr_solve(current_problem, current_placement, self.cr_timeout)
                print("CONTINUOUS REASONING OK, prolog solving time: {:.3f}s".format(prolog_solving_time))

            except UnsatisfiableContinuousReasoning: # or timeout; name it better
                print("CONTINUOUS REASONING FAIL")

                try:
                    current_placement = self.opt.opt_solve(current_problem, self.opt_timeout)
                    print("OPTIMAL REASONING OK")

                except UnsatisfiablePlacement:
                    print("OPTIMAL REASONING FAIL")
                    self.__cleanup__()
                    sys.exit(0)

            current_step += 1
            print("Solving shot: {:.3f}, cost {}".format((time.time() - now) - net_preprocessing_time, current_placement.cost))

            now = time.time()

        self.__cleanup__()

        return
