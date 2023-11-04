from abc import ABC, abstractmethod
from declace.model import Problem, Placement


class ContinuousReasoningService(ABC):
    @abstractmethod
    def cr_solve(self, problem: Problem, placement: Placement, timeout: float) -> Placement:
        pass


class OptimalReasoningService(ABC):
    @abstractmethod
    def opt_solve(self, problem: Problem, timeout: float) -> Placement:
        pass
