from dataclasses import dataclass, field
import uuid
from .region import Region


@dataclass
class RegionGroup(object):
    _id: uuid.UUID = field(default_factory=uuid.uuid1)
    group: str = field(default_factory=str)
    regions: 'list[Region]' = field(default_factory=list)
    beta: float = 0
    var: float = 0

    @staticmethod
    def from_dict(item: dict):
        n = RegionGroup(**item)
        n.regions = [Region(**r) for r in item['regions']]
        n.beta = float(n.beta)
        n.var = float(n.var)
        return n
