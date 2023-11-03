from typing import Tuple

from swiplserver import PrologMQI
from dataclasses import dataclass


@dataclass(frozen=True)
class PrologQuery:
    predicate_name: str
    vars: Tuple[str, ...]

    def __str__(self):
        return "{}({})".format(self.predicate_name, ",".join(self.vars))


def solve_prolog(programs, query, timeout=60):
    # TODO: Non ho capito un cazzo
    # Vorrei usarlo così:
    # solve_prolog('prog.lp', PrologQuery('declace',('P','Time','Cost')))

    result = None
    with PrologMQI() as mqi:
        with mqi.create_thread() as prolog_thread:
            result = prolog_thread.query(str(query), query_timeout_seconds=timeout)
    mqi.stop()

    return result
