from abc import ABC, abstractmethod
from typing import Optional

from declace.model import Problem, Placement


class CIPPReasoningService(ABC):
    def __init__(self, start_placement: Optional[Placement]):
        self.previous_placement = start_placement

    def update_placement(self, placement: Placement):
        print("UPDATING PREVIOUS CR PLACEMENT")
        self.previous_placement = placement

    def invalidate_placement(self):
        print("INVALIDATING PREVIOUS CR PLACEMENT")
        self.previous_placement = None

    @property
    def placement(self):
        return self.previous_placement

    @abstractmethod
    def cr_solve(self, problem: Problem, timeout: int) -> Placement:
        pass


class OIPPReasoningService(ABC):
    @abstractmethod
    def opt_solve(self, problem: Problem, timeout: int) -> Placement:
        pass
