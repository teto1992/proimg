import sys
import time
from pathlib import Path
from typing import List, Tuple

from numpy.random import RandomState

from declace.api.prolog import PrologQuery
from declace.exceptions import UnsatisfiableContinuousReasoning, UnsatisfiablePlacement
from declace.model import Problem, PRECISION
from declace.reasoners.cr.prolog_cr import PrologContinuousReasoningService
from declace.reasoners.opt.asp_opt import ASPOptimalReasoningService
from declace.reasoners.opt.prolog_heu import PrologHeuristicReasoningService

from declace_simulation_framework.simulator.saboteurs import InstanceSaboteur
from declace_simulation_framework.utils.network_utils import (
    prune_network,
    snapshot_closure,
)
from declace_simulation_framework.utils import Stopwatch
import csv

from loguru import logger

LOG_LEVEL_NAME = "PAPER_SIMULATOR"
logger.level(LOG_LEVEL_NAME, no=15, color="<blue>")


class PaperBenchmarkSimulator:
    def __init__(
        self,
        problem: Problem,
        saboteur: InstanceSaboteur,
        shutdown_probability: float,
        cr_timeout: int,
        opt_timeout: int,
        random_state: RandomState,
        output_filename: str
    ):

        self.original_problem = problem
        self.saboteur = saboteur
        self.shutdown_probability = shutdown_probability

        self.asp_scratch = ASPOptimalReasoningService(PRECISION)
        self.prolog_cr = PrologContinuousReasoningService()
        self.prolog_scratch = PrologHeuristicReasoningService()

        self.cr_timeout = cr_timeout
        self.opt_timeout = opt_timeout

        self.random_state = random_state
        self.output_filename = output_filename

    def __cleanup__(self):
        self.prolog_scratch.cleanup()
        self.prolog_cr.cleanup()

    def ruin(self):
        pruned_network = prune_network(self.original_problem.network, self.shutdown_probability, self.random_state)
        closure = snapshot_closure(pruned_network)
        current_problem = self.original_problem.change_underlying_network(closure)
        return current_problem

    def simulate(self, n):
        log_file = Path(self.output_filename).open('w')
        writer = csv.DictWriter(
            log_file,
            delimiter=',',
            quoting=csv.QUOTE_ALL,
            quotechar="\"",
            fieldnames=(
                'step',
                'asp_time',
                'asp_cost',
                'heu_time',
                'heu_cost',
                'cr_time',
                'cr_cost',
                'asp_placement',
                'heu_placement',
                'cr_placement'
            )
        )
        writer.writeheader()

        stopwatch = Stopwatch(5)

        problem = self.ruin()

        try:
            with stopwatch.trigger('asp'):
                asp_placement, asp_stats = self.asp_scratch.opt_solve(problem, self.opt_timeout)
                self.prolog_cr.inject_placement(asp_placement)
        except:
            # Unsatisfiable instance: stop
            pass


        try:
            with stopwatch.trigger('heu'):
                heu_placement, heu_stats = self.prolog_scratch.opt_solve(problem, self.opt_timeout)
        except:
            pass

        writer.writerow({
            'step': 0,
            'asp_time': stopwatch.get('asp'),
            'asp_cost': asp_placement.cost,
            'heu_time': stopwatch.get('heu'),
            'heu_cost': heu_placement.cost,
            'cr_time': stopwatch.get('asp'),
            'cr_cost': asp_placement.cost,
            'asp_placement': asp_placement.as_pairs if asp_placement is not None else None,
            'heu_placement': heu_placement.as_pairs if heu_placement is not None else None,
            'cr_placement': asp_placement.as_pairs if asp_placement is not None else None,
        })
        log_file.flush()

        for step in range(1, n):
            problem = self.ruin()
            stopwatch.clear()
            row = {'step': step}

            try:
                with stopwatch.trigger('asp'):
                    asp_placement, asp_stats = self.asp_scratch.opt_solve(problem, self.opt_timeout)
                row['asp_cost'] = asp_placement.cost
            except:
                row['asp_cost'] = -1
                asp_placement = None
            row['asp_time'] = stopwatch.get('asp')

            try:
                with stopwatch.trigger('cr'):
                    cr_placement, cr_stats = self.prolog_cr.cr_solve(problem, self.cr_timeout)
                row['cr_cost'] = cr_placement.cost
                row['cr_time'] = stopwatch.get('cr')
            except:
                if asp_placement is None:
                    row['cr_time'] = stopwatch.get('cr') + stopwatch.get('asp')
                    row['cr_cost'] = -1
                    cr_placement = None
                else:
                    row['cr_time'] = stopwatch.get('cr') + stopwatch.get('asp')
                    row['cr_cost'] = row['asp_cost']
                    cr_placement = asp_placement
                    self.prolog_cr.inject_placement(asp_placement)

            try:
                with stopwatch.trigger('heu'):
                    self.prolog_scratch.prolog_server.thread.query("retractall(placedImages(_,_,_))")
                    heu_placement, heu_stats = self.prolog_scratch.opt_solve(problem, self.opt_timeout)
                row['heu_cost'] = heu_placement.cost
            except:
                row['heu_cost'] = -1
                heu_placement = None
            row['heu_time'] = stopwatch.get('heu')

            row['asp_placement'] = asp_placement.as_pairs if asp_placement is not None else None
            row['heu_placement'] = heu_placement.as_pairs if heu_placement is not None else None
            row['cr_placement'] = cr_placement.as_pairs if cr_placement is not None else None

            writer.writerow(row)
            log_file.flush()

            if asp_placement is None:
                print("Stop! Unsatisfiable.")
                log_file.close()
                self.__cleanup__()
                sys.exit(0)

        log_file.close()
        self.__cleanup__()
