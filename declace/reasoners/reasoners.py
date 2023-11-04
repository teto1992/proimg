from abc import ABC, abstractmethod
from declace.model import Problem, Placement


class CIPPReasoningService(ABC):
    @abstractmethod
    def cr_solve(self, problem: Problem, placement: Placement, timeout: int) -> Placement:
        pass


class OIPPReasoningService(ABC):
    @abstractmethod
    def opt_solve(self, problem: Problem, timeout: int) -> Placement:
        pass
