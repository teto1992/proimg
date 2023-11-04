import sys
from numpy.random import RandomState

from declace.model import Image, Problem
from declace_simulation_framework.generator.topology import BarabasiAlbert
from declace_simulation_framework.generator.attribute import UniformDiscrete, MultiModal, UniformContinuous
from declace_simulation_framework.generator import LinkGenerator, NodeGenerator, NetworkGenerator
from declace_simulation_framework.simulator import Simulator, InstanceSaboteur, NodeStorageWobble, \
    LinkTiedLatencyBandwidthWobble, ImageSizeWobble

if __name__ == '__main__':
    r = RandomState(77)

    g = NetworkGenerator(
        BarabasiAlbert(n=10, m=1),
        NodeGenerator(
            storage=MultiModal(
                (UniformDiscrete(250, 500, 750), 0.2),
                (UniformDiscrete(100, 150, 200), 0.8)
            ),
            cost=UniformDiscrete(1, 2, 3, 4)
        ),
        LinkGenerator(
            latency=UniformDiscrete(1, 2, 3),
            bandwidth=UniformDiscrete(200, 300, 400, 500)
        )
    )

    saboteur = InstanceSaboteur(
        NodeStorageWobble(UniformContinuous(-0.05, 0.05)),
        LinkTiedLatencyBandwidthWobble(UniformContinuous(-0.02, 0.08)),
        ImageSizeWobble(UniformContinuous(0.05, 0.10))
    )

    images = [
        Image("ubuntu", 3, 1000.0),
        Image("busybox", 5, 2000.0)
    ]

    simulator = Simulator(
        Problem(images, g.generate(r), 50),
        saboteur,
        0.01,
        2,
        5
    )

    simulator.simulate(5, r)

