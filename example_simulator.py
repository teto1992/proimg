import sys
from numpy.random import RandomState
from argparse import ArgumentParser

from declace.model import Image, Problem
from declace_simulation_framework.generator.topology import (
    BarabasiAlbert,
    ErdosRenyi,
    TruncatedBarabasiAlbert,
    RandomInternet,
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
        #TruncatedBarabasiAlbert(n=200, m=3, k=5),
        BarabasiAlbert(n=100, m=3),
        #RandomInternet(n=100),
        NodeGenerator(
            storage=MultiModal(
                (UniformDiscrete(4096, 8092), 0.2),
                (UniformDiscrete(512, 1024, 2048), 0.8),
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
        #Image("python", 1020, 90),
        # Image("busybox", 4, 30),
        # Image("redis", 149, 60),
        Image("postgres", 438, 90),
        # Image("httpd", 195, 60),
        # Image("node", 1100, 90),
        # Image("mongo", 712, 30),
        # Image("mysql", 621, 60),
        # Image("memcached", 126, 30),
        # Image("traefik", 148, 50),
        # Image("mariadb", 387, 120),
        # Image("rabbitmq", 201, 100),
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
