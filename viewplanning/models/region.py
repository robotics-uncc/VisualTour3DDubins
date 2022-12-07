from dataclasses import dataclass, field
import numpy as np
from enum import IntEnum


class RegionType(IntEnum):
    UNKNOWN = 0
    POLYGON = 1
    WAVEFRONT = 2
    POINT = 3


@dataclass
class Region(object):
    type: RegionType = RegionType.UNKNOWN
    file: str = field(default_factory=str)
    rotationMatrix: 'list[list[float]]' = field(default_factory=lambda: np.eye(3).tolist())
    z: float = 0
    points: 'list[list[float]]' = field(default_factory=list)
    verificationRegion: str = field(default_factory=str)
