from enum import IntEnum
from dataclasses import dataclass, field


class SampleStrategyType(IntEnum):
    UNKNOWN = 0
    FACE = 1
    BODY = 3
    POINT = 5
    WEIGHTED_FACE = 6
    GLOBAL_WEIGHTED_FACE = 7
    MAX_AREA_EDGE = 8
    EDGE_3D = 11
    MAX_AREA_POLYGON = 12


@dataclass
class SampleStrategyRecord(object):
    type: SampleStrategyType = SampleStrategyType.UNKNOWN
    numSamples: int = 1
    numTheta: int = 1
    numPhi: int = 1
    phiRange: 'list[float]' = field(default_factory=lambda: [0, 0])
    hyperParameters: 'list[float]' = field(default_factory=list)
