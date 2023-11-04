from abc import ABC, abstractmethod
from declace.model import Problem, Placement


class ContinuousReasoningService(ABC):
    @abstractmethod
    def opt_solve(self, problem: Problem, placement: Placement) -> Placement:
        pass


class OptimalReasoningService(ABC):
    @abstractmethod
    def cr_solve(self, problem: Problem) -> Placement:
        pass
