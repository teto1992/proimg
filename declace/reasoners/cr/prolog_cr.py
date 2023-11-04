from pathlib import Path

from declace.api.prolog.prolog_server import PrologServer
from declace.model import Problem, Placement
from declace.reasoners import ContinuousReasoningService


class PrologContinuousReasoningService(ContinuousReasoningService):
    def __init__(self, prolog_encoding: Path, verbose_server=True):
        self.prolog_server: PrologServer = PrologServer(prolog_encoding, verbose=verbose_server)

    def cr_solve(self, problem: Problem, placement: Placement) -> Placement:

        # TODO: Non mi piace, chi si ricorda di fare stop del Prolog server?
        if not self.prolog_server.alive:
            self.prolog_server.start()

        # Write problem into infra/images temp file...

        # Write placement into temp file...

        # Load to PrologServer

        # Query PrologServer for declare(P,Cost,Time)

        # Parse result into a placement object

        return None
