import dataclasses
import math
import typing
from math import ceil


def fixed_precision(value, precision):
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
            fixed_precision(self.latency, precision),
            fixed_precision(self.bandwidth, precision),
        )


@dataclasses.dataclass(frozen=True)
class Image:
    id: str
    size: int
    max_transfer_time: float

    @property
    def atom(self, precision=3):
        return "image({}, {}, {})".format(
            self.id, self.size, fixed_precision(self.max_transfer_time, precision)
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
            string.append("Images placed on {}: {}".format(node, [i for i in images]))
        return "\n".join(string)


@dataclasses.dataclass(frozen=True)
class Problem:
    images: typing.Iterable[Image]
    network: NetworkSnapshot
    max_replicas: int = 6

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