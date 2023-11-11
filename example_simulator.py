import sys
from numpy.random import RandomState
from argparse import ArgumentParser

from declace.model import Image, Problem
from declace_simulation_framework.generator.topology import (
    BarabasiAlbert,
    ErdosRenyi,
    TruncatedBarabasiAlbert,
)
from declace_simulation_framework.generator.attribute import (
    UniformDiscrete,
    MultiModal,
    UniformContinuous,
)
from declace_simulation_framework.generator import (
    LinkGenerator,
    NodeGenerator,
    NetworkGenerator,
)
from declace_simulation_framework.simulator import (
    Simulator,
    InstanceSaboteur,
    NodeStorageWobble,
    LinkTiedLatencyBandwidthWobble,
    ImageSizeWobble, PaperBenchmarkSimulator,
)
from declace_simulation_framework.simulator.saboteurs import NullSaboteur
from declace.utils import enable_logging_channels

from loguru import logger
import loguru


def show_level(record):
    print("MESSAGE_LEVEL: ", record["level"].name)
    print(record)
    return True


if __name__ == "__main__":
    import sys
    enable_logging_channels(["DISABLE_LOGGING"])

    if len(sys.argv) != 3:
        print("Usage: {} [log file] [seed]".format(__file__))

    outputfile, seed = sys.argv[1:]

    r = RandomState(seed)

    g = NetworkGenerator(
        # TruncatedBarabasiAlbert(n=1000, m=3, k=5),
        BarabasiAlbert(n=250, m=3),
        NodeGenerator(
            storage=MultiModal(
                (UniformDiscrete(64000, 128000, 256000, 512000), 0.2),
                (UniformDiscrete(8000, 16000, 32000), 0.8),
            ),
            cost=UniformDiscrete(1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
        ),
        LinkGenerator(
            latency=UniformDiscrete(*list(range(1, 21))),
            bandwidth=UniformDiscrete(*list(range(5, 500))),
        ),
    )

    saboteur = InstanceSaboteur(
        NodeStorageWobble(UniformContinuous(-0.20, 0.20)),
        LinkTiedLatencyBandwidthWobble(UniformContinuous(-0.25, 0.25)),
        ImageSizeWobble(UniformContinuous(-0.10, 0.10)),
    )

    images = [
        Image("alpine", 8, 30),
        Image("ubuntu", 69, 60),
        Image("nginx", 192, 120),
    ]

    original_problem = Problem(images, g.generate(r), max_replicas=10)

    simulator = PaperBenchmarkSimulator(
        original_problem,
        saboteur,
        0.15,
        2,
        60,
        r,
        outputfile
    )

    simulator.simulate(100)
