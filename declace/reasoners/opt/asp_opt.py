from declace.model import Problem, Placement
from declace.reasoners import OptimalReasoningService


class ASPOptimalReasoningService(OptimalReasoningService):
    def opt_solve(self, problem: Problem, timeout: float) -> Placement:
        # Initialize a Clingo

        # Serialize problem into a set of facts

        # Run the solver

        # Parse the answer back into a Placement

        return None
