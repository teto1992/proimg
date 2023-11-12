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
        #TruncatedBarabasiAlbert(n=50, m=3, k=5),
        # ErdosRenyi(n=50, p=0.05),
        BarabasiAlbert(n=100, m=3),
        #RandomInternet(n=1000),
        NodeGenerator(
            storage=MultiModal(
                (UniformDiscrete(16000, 32000), 0.2),
                (UniformDiscrete(2000, 4000, 8000), 0.8),
            ),
            cost=UniformDiscrete(1, 2, 3, 4, 5, 6, 7),
        ),
        LinkGenerator(
            latency=UniformDiscrete(*list(range(1, 16))),
            bandwidth=UniformDiscrete(*list(range(5, 251))),
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
        Image("nginx", 192, 60),
        #Image("python", 1020, 120),
        # Image("busybox", 4, 30),
        # Image("redis", 149, 60),
        #Image("postgres", 438, 60),
        #Image("httpd", 195, 60),
        # Image("node", 1100, 90),
        # Image("mongo", 712, 30),
        # Image("mysql", 621, 60),
        # Image("memcached", 126, 30),
        # Image("traefik", 148, 50),
        # Image("mariadb", 387, 120),
        # Image("rabbitmq", 201, 100),
    ]

    original_problem = Problem(images, g.generate(r), max_replicas=6)

    simulator = PaperBenchmarkSimulator(
        original_problem,
        saboteur,
        0.15,
        10,
        60,
        r,
        outputfile
    )

    simulator.simulate(100)
