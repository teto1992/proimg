"""
initial_network = ...
initial_requirements = ...

initial_placement = ...
for step in range(t):
    apply saboteurs
    placement = solve_incremental(network, placement)

    if timeout:
        scratch_placement = solve_optimal_scratch(network)
"""
from declace.model import Problem
from declace_simulation_framework.simulator.saboteurs import InstanceSaboteur
from declace_simulation_framework.utils.network_utils import (
    prune_network,
    snapshot_closure,
)


class Simulator:
    def __init__(
        self, problem: Problem, saboteur: InstanceSaboteur, shutdown_probability: float
    ):
        self.original_problem = problem
        self.saboteur = saboteur
        self.shutdown_probability = shutdown_probability

    def simulate(self, n, random_state):
        pruned_network = prune_network(
            self.original_problem.network, self.shutdown_probability, random_state
        )
        closure = snapshot_closure(pruned_network)

        current_network = closure

        # solve from scratch with ASP
        # solve_asp(network, images) --> returns best_known within timeout budget
        (placement, satisfiable), stats = solve_asp(
            Problem(network, self.original_problem.images), ...
        )

        current_step = 0
        while current_step < n:
            # Apply saboteurs + Network closure
            current_network = prune_network(
                self.original_problem.network, self.shutdown_probability, random_state
            )
            problem = self.saboteur.ruin(
                Problem(self.original_problem.images, current_network), random_state
            )
            current_network = snapshot_closure(problem.network)

            (new_placement, satisfiable), stats = solve_prolog(
                Problem(problem.images, current_network), ...
            )

        return stats
