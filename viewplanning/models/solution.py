from dataclasses import dataclass, field
import uuid
from .experiment import Experiment
from .edge import Edge
from .vertex import Vertex


@dataclass
class Solution(object):
    cost: float = 0
    executionTime: float = 0
    edges: 'list[Edge]' = field(default_factory=list)
    experiment: Experiment = field(default_factory=Experiment)
    executed: bool = False
    _id: uuid.UUID = field(default_factory=uuid.uuid1)
    samples: 'list[Vertex]' = field(default_factory=list)
    verified: int = 0

    @staticmethod
    def from_dict(item: dict):
        n = Solution(**item)
        n.edges = [Edge.from_dict(e) for e in item['edges']]
        n.experiment = Experiment.from_dict(item['experiment'])
        n.samples = [Vertex.from_dict(v) for v in item['samples']]
        n.verified = int(n.verified)
        return n
