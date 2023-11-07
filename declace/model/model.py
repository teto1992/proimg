import dataclasses
import math
import typing
from math import ceil


def fixed_precision(value, precision, inf):
    if math.isinf(value):
        return inf

    return int(math.ceil(value * 10**precision))


@dataclasses.dataclass(frozen=True)
class Node:
    id: int
    storage: int
    cost: float

    @property
    def atom(self, precision=3):
        return "node(n{},{},{})".format(self.id, self.storage, self.cost)


@dataclasses.dataclass(frozen=True)
class Link:
    source: int
    target: int
    latency: float
    bandwidth: float

    @property
    def atom(self, precision=3):
        return "link(n{}, n{}, {}, {})".format(
            self.source,
            self.target,
            fixed_precision(self.latency, precision, inf=9999),
            fixed_precision(self.bandwidth, precision, inf=1),
        )


@dataclasses.dataclass(frozen=True)
class Image:
    id: str
    size: int
    max_transfer_time: float

    @property
    def atom(self, precision=3):
        return "image({}, {}, {})".format(
            self.id, self.size, fixed_precision(self.max_transfer_time, precision, None)
        )


@dataclasses.dataclass(frozen=True)
class NetworkSnapshot:
    nodes: typing.Iterable[Node]
    links: typing.Iterable[Link]

    def __str__(self):
        string = [
            "A network on {} nodes and {} links.".format(
                len(self.nodes), len(self.links)
            )
        ]
        string.append("Nodes:\n")
        for node in self.nodes:
            string.append(
                "\t[{}] - {:.3f} MB, {:.3f} €/MB\n".format(
                    node.id, node.storage, node.cost
                )
            )

        string.append("Links:\n")
        for link in self.links:
            string.append(
                "\t{} -- {} - {:.3f}ms {:.3f}MB/s\n".format(
                    link.source, link.target, link.latency, link.bandwidth
                )
            )

        return "".join(string)


@dataclasses.dataclass(frozen=True)
class Placement:
    cost: float
    placement: typing.Dict[int, typing.Iterable[Image]]

    def __str__(self):
        string = ["A solution with cost {}.".format(self.cost)]
        for node, images in self.placement.items():
            string.append("Images placed on {}: {}".format(node, [i.id for i in images]))
        return "\n".join(string)

    @property
    def as_facts(self):
        prg = []
        for node_id, images in self.placement.items():
            for image in images:
                # at(0, 'alpine')
                prg.append("at({}, {}).".format(image, node_id))
        return "\n".join(prg)


@dataclasses.dataclass(frozen=True)
class Problem:
    images: typing.Iterable[Image]
    network: NetworkSnapshot
    max_replicas: int

    @property
    def as_facts(self):
        prg = [
            "max_replicas({}).".format(self.max_replicas),
            "maxReplicas({}).".format(self.max_replicas),
        ]

        for image in self.images:
            prg.append("{}.".format(image.atom))

        for node in self.network.nodes:
            prg.append("{}.".format(node.atom))

        for link in self.network.links:
            prg.append("{}.".format(link.atom))

        return "\n".join(prg)

    def change_underlying_network(self, network: NetworkSnapshot) -> 'Problem':
        return Problem(self.images, network, self.max_replicas)
