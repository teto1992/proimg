from collections import defaultdict
from pathlib import Path
from typing import List, Iterable

from declace.api.prolog import PrologServer, PrologDatafile, PrologQuery, PrologPredicate
from declace.model import Problem, Placement, Image, NetworkSnapshot
from declace.reasoners import CIPPReasoningService

import tempfile


class PrologContinuousReasoningService(CIPPReasoningService):
    def __init__(self, prolog_encoding: Path, verbose_server=True):
        self.prolog_server: PrologServer = PrologServer(prolog_encoding, verbose=verbose_server)
        self.scratch_directory = tempfile.TemporaryDirectory()

    def __del__(self):
        if self.prolog_server.alive:
            self.prolog_server.stop()

        self.scratch_directory.cleanup()

    def _dump_problem(self, problem: Problem):
        with Path(self.scratch_directory.name, 'instance.pl').open('w') as f:
            f.write(problem.as_facts)
            f.flush()

    def _load_problem(self):
        data = PrologDatafile(
            path=Path(self.scratch_directory.name, 'instance.pl'),
            retractions = PrologPredicate.from_strings(
                "node/3", "link/4", "image/3", "maxReplicas/1"
            )
        )

        self.prolog_server.load_datafile(data)

    def _ans_to_obj(self, query_result):
        image_to_nodes = defaultdict(lambda: [], dict())
        for atom in query_result['P']:
            image, node = atom['args']
            image_to_nodes[image].append(node)
        return image_to_nodes

    def cr_solve(self, problem: Problem, placement: Placement, timeout: int) -> Placement:
        if not self.prolog_server.alive:
            self.prolog_server.start()

        # Write to tempfile & load to PrologServer
        self._dump_problem(problem)
        self._load_problem()

        # Query PrologServer for declare(P,Cost,Time)
        result = self.prolog_server.query(PrologQuery.from_string("declace", "P,Cost,Time"), timeout=timeout)

        # Parse result into a placement object
        return Placement(
            cost=result['Cost'],
            placement=self._ans_to_obj(result)
        )
