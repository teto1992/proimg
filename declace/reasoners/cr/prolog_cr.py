from collections import defaultdict
from pathlib import Path
from declace.api.prolog import (
    PrologServer,
    PrologDatafile,
    PrologQuery,
    PrologPredicate,
)
from declace.exceptions import UnsatisfiableContinuousReasoning
from declace.model import Problem, Placement
from declace.reasoners import CIPPReasoningService
import swiplserver

import tempfile


class PrologContinuousReasoningService(CIPPReasoningService):
    SOURCE_FOLDER = Path(__file__).parent / 'prolog_cr_source'

    def __init__(self, verbose_server=True):
        src = PrologContinuousReasoningService.SOURCE_FOLDER
        self.prolog_server: PrologServer = PrologServer(
            src / 'config.pl', src / 'main.pl', verbose=verbose_server
        )
        self.scratch_directory = tempfile.TemporaryDirectory()

    def __del__(self):
        if self.prolog_server.alive:
            self.prolog_server.stop()

        self.scratch_directory.cleanup()

    def _set_up_datafile(self, problem: Problem, placement: Placement):
        with Path(self.scratch_directory.name, "instance.pl").open("w") as f:
            f.write(problem.as_facts + "\n")
            f.write(placement.as_facts + "\n")
            f.flush()

        data = PrologDatafile(
            path=Path(self.scratch_directory.name, "instance.pl"),
            retractions=PrologPredicate.from_strings(
                "node/3", "link/4", "image/3", "maxReplicas/1"
            ),
        )

        self.prolog_server.load_datafile(data)

    def _ans_to_obj(self, query_result):
        image_to_nodes = defaultdict(lambda: [], dict())
        for atom in query_result["P"]:
            image, node = atom["args"]
            image_to_nodes[image].append(node)
        return Placement(query_result["Cost"], image_to_nodes)

    def cr_solve(
        self, problem: Problem, placement: Placement, timeout: int
    ) -> Placement:
        if not self.prolog_server.alive:
            self.prolog_server.start()

        # Write to tempfile & load to PrologServer
        self._set_up_datafile(problem, placement)

        # Query PrologServer for declare(P,Cost,Time)
        try:
            query_result = self.prolog_server.query(
                PrologQuery.from_string("declace", "P,Cost,Time"), timeout=timeout
            )

        except swiplserver.PrologQueryTimeoutError:
            raise UnsatisfiableContinuousReasoning()

        except swiplserver.PrologError as e:
            raise RuntimeError("A Prolog error that is unrelated to timeouts:", e)

        # Parse result into a placement object
        return self._ans_to_obj(query_result)
