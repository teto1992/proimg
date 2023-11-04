import sys

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
            verbose = True
    ):
        self.original_problem = problem
        self.saboteur = saboteur
        self.shutdown_probability = shutdown_probability

        self.opt = ASPOptimalReasoningService()
        self.cr = PrologContinuousReasoningService(True)

        self.cr_timeout = cr_timeout
        self.opt_timeout = opt_timeout

        self.verbose = verbose

    def __cleanup__(self):
        self.cr.cleanup()
        self.opt.cleanup()

    def simulate(self, n, random_state):
        # Solving OIPP
        pruned_network = prune_network(
            self.original_problem.network, self.shutdown_probability, random_state
        )


        closure = snapshot_closure(pruned_network)

        current_problem = self.original_problem.change_underlying_network(closure)


        current_placement = self.opt.opt_solve(current_problem, self.opt_timeout)
        #
        print("Solving...?")

        print(current_placement)

        current_step = 1
        while current_step < n:
            print("Current placement [{}]:".format(current_step))
            print(current_placement)
            # Apply saboteurs + Network closure
            current_network = prune_network(
                self.original_problem.network, self.shutdown_probability, random_state
            )
            problem = self.saboteur.ruin(
                current_problem.change_underlying_network(current_network), random_state
            )

            try:
                current_network = snapshot_closure(problem.network)
                current_problem = problem.change_underlying_network(current_network)
                current_placement = self.cr.cr_solve(current_problem, current_placement, self.cr_timeout)
            except UnsatisfiableContinuousReasoning:
                print("Continuous Reasoning timeout! Calling ASP.")
                try:
                    current_placement = self.opt.opt_solve(current_problem, self.opt_timeout)
                except UnsatisfiablePlacement:
                    print("No solution exists for this configuration.")
                    self.__cleanup__()
                    sys.exit(0)

            current_step += 1

        print("Current placement:")
        print(current_placement)

        self.__cleanup__()

        return
