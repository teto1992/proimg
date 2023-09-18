import sys
import pathlib
import logging
import json

import clingo
import argparse
from collections import defaultdict

from math import ceil

ENCODING = (pathlib.Path(__file__).parent / "encoding.lp").as_posix()


def write(string, target):
    # https://stackoverflow.com/questions/17602878/how-to-handle-both-with-open-and-sys-stdout-nicely
    sys.stdout.close = lambda: None
    with (open(target, "w") if target else sys.stdout) as hnd:
        hnd.write(string)


class Messages:
    TRANSFER_TIME_COMPUTATION = (
        "Computing @-term: compute_transfer_time({},{},{}) = {} ~ {}"
    )
    INTERMEDIATE_SOLUTION = "Found a solution with cost {}, optimal? {}, model: \n{}"


class Context:
    def __init__(self, debug=False, precision=None):
        # TODO: Unità di misura, cifre aritmetica
        self.precision = precision
        self.debug = debug

    def compute_transfer_time(self, size, bandwith, latency):
        # latency.number / 1000 ms -> s
        r_seconds = float(size.number) * float(8.0) / float(bandwith.number) + float(latency.number) / 1000.0
        r_milliseconds = r_seconds * 1000.0

        if self.debug:
            logging.debug(
                Messages.TRANSFER_TIME_COMPUTATION.format(
                    size, bandwith, latency, r_milliseconds, ceil(r_milliseconds)
                )
            )

        return clingo.Number(int(ceil(r_milliseconds)))


def project_answer_set(model):
    return [sym for sym in model.symbols(atoms=True) if sym.match("placement", 2)]


class SolutionCallback:
    def __init__(self, debug=False):
        self._placement = None
        self._cost = None
        self.debug = debug

    def __call__(self, model):
        atoms = project_answer_set(model)
        if self.debug:
            prg = "\n".join("{}.".format(str(x)) for x in atoms)
            logging.debug(
                Messages.INTERMEDIATE_SOLUTION.format(
                    model.cost, model.optimality_proven, prg
                )
            )

        if not model.optimality_proven:
            return True

        self._placement = atoms
        self._cost = model.cost
        return False

    @property
    def as_json(self):
        image_to_nodes = defaultdict(lambda: [])
        if self._placement is None:
            # Never met a model, unsat
            return json.dumps({"satisfiable": False}, indent=2)

        for symbol in self._placement:
            img = symbol.arguments[0].name
            node = symbol.arguments[1].name
            image_to_nodes[img].append(node)

        return json.dumps(
            {
                "satisfiable": True,
                "cost": self._cost,
                "placement": [
                    {"image": image, "nodes": nodes}
                    for image, nodes in image_to_nodes.items()
                ],
            },
            indent=2,
        )


# TODO: Parsing available images into atoms?
# TODO: Parsing infrastructure into atoms?


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "infrastructure", type=str, help="File describing network architecture."
    )
    p.add_argument("images", type=str, help="File with images to be placed.")
    p.add_argument("-d", "--debug", action="store_true")
    p.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Save optimal solution to file as a JSON.",
    )
    args = p.parse_args()

    return args


if __name__ == "__main__":
    args = parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    ctl = clingo.Control(["--models=1", "--opt-mode=optN"])

    ctl.load(ENCODING)
    ctl.load(args.infrastructure)
    ctl.load(args.images)

    ctl.ground([("base",[])], context=Context(args.debug))

    s = SolutionCallback(args.debug)
    ans = ctl.solve(on_model=s)

    write(s.as_json, args.output)
