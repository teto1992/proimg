import sys
from numpy.random import RandomState

from declace.model import Image, Problem
from declace_simulation_framework.generator.topology import BarabasiAlbert, ErdosRenyi, TruncatedBarabasiAlbert
from declace_simulation_framework.generator.attribute import UniformDiscrete, MultiModal, UniformContinuous
from declace_simulation_framework.generator import LinkGenerator, NodeGenerator, NetworkGenerator
from declace_simulation_framework.simulator import Simulator, InstanceSaboteur, NodeStorageWobble, \
    LinkTiedLatencyBandwidthWobble, ImageSizeWobble

if __name__ == '__main__':
    r = RandomState(1)

    g = NetworkGenerator(
        TruncatedBarabasiAlbert(n=500, m=3, k=3),
        #ErdosRenyi(n=100, p=0.05),
        NodeGenerator(
            storage=MultiModal(
                (UniformDiscrete(64000, 128000, 256000, 512000), 0.2),
                (UniformDiscrete(8000, 16000, 32000), 0.8)
            ),
            cost=UniformDiscrete(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
        ),
        LinkGenerator(
            latency=UniformDiscrete(*list(range(1,21))),
            bandwidth=UniformDiscrete(*list(range(5, 500)))
        )
    )

    saboteur = InstanceSaboteur(
        NodeStorageWobble(UniformContinuous(-0.20, 0.20)),
        LinkTiedLatencyBandwidthWobble(UniformContinuous(-0.25, 0.25)),
        ImageSizeWobble(UniformContinuous(-0.10, 0.10))
    )

    images = [
        Image("alpine", 8, 30.0),
        Image("ubuntu", 69, 60.0),
        Image("nginx", 192, 120.0)
    ]

    original_problem = Problem(images, g.generate(r), max_replicas=10)

    simulator = Simulator(
        original_problem,
        saboteur,
        0.12,
        2,
        5,
        verbose=True
    )

    simulator.simulate(100, r)

