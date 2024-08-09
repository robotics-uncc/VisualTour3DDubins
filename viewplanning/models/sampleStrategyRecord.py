from enum import IntEnum
from dataclasses import dataclass, field


class SampleStrategyType(IntEnum):
    UNKNOWN = 0
    FACE = 1
    BODY = 3
    POINT = 5
    GLOBAL_WEIGHTED_FACE = 7
    MAX_AREA_EDGE = 8
    EDGE_3D = 11
    MAX_AREA_POLYGON = 12


class SampleStrategyIntersection(IntEnum):
    UNKNOWN = 0
    NON_INTERSECTING = 1
    SIMPLE_INTERSECTION = 2
    BRUTE_INTERSECTION = 4


class HeadingStrategyType(IntEnum):
    UNKNOWN = 0
    UNIFORM = 1
    INWARD = 2
    DWELL = 3


@dataclass
class IntersectionStrategyRecord(object):
    type: SampleStrategyIntersection = SampleStrategyIntersection.NON_INTERSECTING
    cliqueLimit: int = 3
    alpha: float = 1.0
    cliqueRadius: float = 300.0


@dataclass
class HeadingStrategyRecord(object):
    type: HeadingStrategyType = HeadingStrategyType.UNKNOWN
    headingRange: 'list[float]' = field(default_factory=list)
    dwellDistance: float = 0.0
    numRays: int = 0
    multiplyDwell: bool = field(default=False)


@dataclass
class SampleStrategyRecord(object):
    type: SampleStrategyType = SampleStrategyType.UNKNOWN
    numSamples: int = 1
    numTheta: int = 1
    numPhi: int = 1
    phiRange: 'list[float]' = field(default_factory=lambda: [0, 0])
    hyperParameters: 'list[float]' = field(default_factory=list)
    intersection: IntersectionStrategyRecord = field(
        default_factory=IntersectionStrategyRecord
    )
    heading: HeadingStrategyRecord = field(
        default_factory=HeadingStrategyRecord
    )

    @staticmethod
    def from_dict(item: dict):
        n = SampleStrategyRecord(**item)
        n.intersection = IntersectionStrategyRecord(
            **item.get('intersection', {})
        )
        n.heading = HeadingStrategyRecord(**item.get('heading', {}))
        return n
