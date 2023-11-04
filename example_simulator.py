import sys
from numpy.random import RandomState

from declace.model import Image, Problem
from declace_simulation_framework.generator.topology import BarabasiAlbert, ErdosRenyi
from declace_simulation_framework.generator.attribute import UniformDiscrete, MultiModal, UniformContinuous
from declace_simulation_framework.generator import LinkGenerator, NodeGenerator, NetworkGenerator
from declace_simulation_framework.simulator import Simulator, InstanceSaboteur, NodeStorageWobble, \
    LinkTiedLatencyBandwidthWobble, ImageSizeWobble

if __name__ == '__main__':
    r = RandomState(1)

    g = NetworkGenerator(
        BarabasiAlbert(n=250, m=5),
        NodeGenerator(
            storage=MultiModal(
                (UniformDiscrete(150, 175, 200), 0.5),
                (UniformDiscrete(50, 75, 100), 0.5)
            ),
            cost=UniformDiscrete(1, 2, 3, 4, 5)
        ),
        LinkGenerator(
            latency=UniformDiscrete(0.5, 1.0, 1.5),
            bandwidth=UniformDiscrete(400, 500, 600)
        )
    )

    saboteur = InstanceSaboteur(
        NodeStorageWobble(UniformContinuous(-0.02, 0.10)),
        LinkTiedLatencyBandwidthWobble(UniformContinuous(-0.05, 0.20)),
        ImageSizeWobble(UniformContinuous(0.0, 0.25))
    )

    images = [
        Image("ubuntu", 5, 120.0),
        Image("busybox", 8, 120.0),
        Image("swipl", 3, 120.0),
    ]

    original_problem = Problem(images, g.generate(r), 100)
    print("Barabasi generato?")

    simulator = Simulator(
        original_problem,
        saboteur,
        0.15,
        2,
        5
    )

    simulator.simulate(100, r)

