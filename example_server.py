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
        BarabasiAlbert(n=1024, m=3),
        # RandomInternet(n=128),
        # WattsStrogatz(n=256, k=4, p=0.1),
        NodeGenerator(
            storage=MultiModal(
                (UniformDiscrete(64000, 128000), 0.2),
                (UniformDiscrete(16000, 32000), 0.5),
                (UniformDiscrete(4000, 8000), 0.3),
            ),
            cost=UniformDiscrete(1, 2, 3, 4, 5),
        ),
        LinkGenerator(
            latency=UniformDiscrete(*list(range(1, 11))),
            bandwidth=UniformDiscrete(*list(range(25, 1001)))
        ),
    )

    saboteur = InstanceSaboteur(
        NodeStorageWobble(UniformContinuous(-0.2, 0.2)),
        LinkTiedLatencyBandwidthWobble(UniformContinuous(-0.2, 0.2)),
        ImageSizeWobble(UniformContinuous(-0.10, 0.10)),
    )

    images = [
        Image("busybox", 4, 15),
        Image("memcached", 126, 30),
        Image("nginx", 192, 30),
        Image("mariadb", 387, 60),

        Image("alpine", 8, 15),
        Image("traefik", 148, 30),
        Image("httpd", 195, 30),
        Image("postgres", 438, 60),

        Image("ubuntu", 69, 15),
        Image("redis", 149, 30),
        Image("rabbitmq", 201, 60),
        Image("mysql", 621, 60),

        # Image("mongo", 712, 120),
        # Image("python", 1020,120),
        # Image("node", 1100, 120),
    ]

    original_problem = Problem(images, g.generate(r), max_replicas=256)

    simulator = PaperBenchmarkSimulator(
        original_problem,
        saboteur,
        0.10,
        15, # cr timeout
        30, # opt timeout
        r,
        outputfile
    )

    simulator.simulate(100)
