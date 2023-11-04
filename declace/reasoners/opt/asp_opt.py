from typing import List, Tuple

import clingo

from declace.model import Problem, Placement
from declace.reasoners import OIPPReasoningService


class ASPOptimalReasoningService(OIPPReasoningService):
    def __init__(self):
        # cost_at_time[i] = (a, b) -> i-th candidate model has cost a, found at time b
        # TODO: Refactor into a Stats class
        self.cost_at_time: List[Tuple[int, float]] = []

    def opt_solve(self, problem: Problem, timeout: int) -> Placement:
        # Initialize a Clingo
        ctl = clingo.Control(["--models=1", "--opt-mode=optN"])

        # Serialize problem into a set of facts
        ctl.load(...)  # encoding
        ctl.add(problem.as_facts)

        # Run the solver
        ctl.ground([("base", [])], context=...)

        # Parse the answer back into a Placement
        with ctl.solve(..., async_=True) as handle:
            handle.wait(timeout)
            ans = handle.get()

        # Logs:
        # Cost of the found placement @ given time seconds
        # The 'last' (also best) found placement within available seconds

        return Placement(...)
