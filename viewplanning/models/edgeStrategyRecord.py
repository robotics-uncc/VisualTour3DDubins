from dataclasses import dataclass, field
from enum import IntEnum
from .etsp2dtspType import Etsp2DtspType


class EdgeStrategyType(IntEnum):
    UNKNOWN = 0
    DUBINS_CAR = 1
    VANA_AIRPLANE = 2
    MODIFIED_AIRPLANE = 3


class EdgeModification(IntEnum):
    NONE = 0
    DWELL = 2
    LEAD_IN_DWELL = 3


@dataclass
class EdgeStrategyRecord:
    type: EdgeStrategyType = EdgeStrategyType.UNKNOWN
    modification: EdgeModification = EdgeModification.NONE
    dwellDistance: float = 0
    leadDistance: float = 0
    etsp2DTSPType: Etsp2DtspType = Etsp2DtspType.UNKNOWN
    radius: float = 0
    flightAngleBounds: 'list[float]' = field(default_factory=lambda: [0] * 2)
