from dataclasses import dataclass, field
import numpy as np
from enum import IntEnum


class RoadMapType(IntEnum):
    UNKNOWN = 0


@dataclass
class Environment(object):
    file: str = ''
    rotationMatrix: 'list[list[float]]' = field(default_factory=lambda: np.eye(3).tolist())
    beta: float = 0
    var: float = 0,
    roadMapType: RoadMapType = field(default=RoadMapType.UNKNOWN)
    sampleDistance: float = 10.0
    inflateRadius: float = 1.0
    numLevels: int = 2
