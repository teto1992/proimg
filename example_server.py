import sys
from numpy.random import RandomState
from argparse import ArgumentParser

from declace.model import Image, Problem
from declace_simulation_framework.generator.topology import (
    BarabasiAlbert,
    ErdosRenyi,
    TruncatedBarabasiAlbert,
    RandomInternet,
    WattsStrogatz,
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
        sys.exit(1)

    outputfile, seed = sys.argv[1:]
    seed = int(seed)

    r = RandomState(seed)

    g = NetworkGenerator(
        # TruncatedBarabasiAlbert(n=256, m=3, k=5),
        # ErdosRenyi(n=512, p=0.05),
        BarabasiAlbert(n=512, m=3),
        # RandomInternet(n=256),
        # WattsStrogatz(n=256, k=4, p=0.1),
        NodeGenerator(
            storage=MultiModal(
                (UniformDiscrete(64000), 0.1),
                (UniformDiscrete(16000, 32000), 0.3),
                (UniformDiscrete(4000, 8000), 0.6),
            ),
            cost=UniformDiscrete(1, 2, 3, 4, 5),
        ),
        LinkGenerator(
            latency=UniformDiscrete(*list(range(1, 16))),
            bandwidth=UniformDiscrete(*list(range(5, 1001))),
        ),
    )

    saboteur = InstanceSaboteur(
        NodeStorageWobble(UniformContinuous(-0.25, 0.25)),
        LinkTiedLatencyBandwidthWobble(UniformContinuous(-0.25, 0.25)),
        ImageSizeWobble(UniformContinuous(-0.10, 0.10)),
    )

    saboteur = NullSaboteur(None, None, None)

    images = [
        Image("alpine", 8, 5),
        Image("ubuntu", 69, 30),
        Image("nginx", 192, 60),
        Image("python", 1020, 120),
        Image("busybox", 4, 30),
        # Image("redis", 149, 10),
        # Image("postgres", 438, 30),
        # Image("httpd", 195, 30),
        # Image("node", 1100, 60),
        # Image("mongo", 712, 30),
        # Image("mysql", 621, 30),
        # Image("memcached", 126, 30),
        # Image("traefik", 148, 30),
        # Image("mariadb", 387, 30),
        # Image("rabbitmq", 201, 30),
    ]

    original_problem = Problem(images, g.generate(r), max_replicas=10)

    simulator = PaperBenchmarkSimulator(
        original_problem,
        saboteur,
        0.10,
        30,
        30,
        r,
        outputfile
    )

    simulator.simulate(100)
