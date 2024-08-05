from dataclasses import dataclass, field
from .vertex import Vertex, Vertex2D, Vertex3D
from .dubinsPathType import DubinsPathType
from enum import IntEnum
import numpy as np


class EdgeType(IntEnum):
    UNKNOWN = 0
    TWO_D = 1
    THREE_D = 2
    DWELL_STRAIGHT = 3
    LEAD_IN_DWELL = 4


@dataclass
class Edge(object):
    start: Vertex = field(default_factory=Vertex)
    end: Vertex = field(default_factory=Vertex)
    cost: float = 0
    type: EdgeType = EdgeType.UNKNOWN

    @staticmethod
    def from_dict(item: dict):
        if item['type'] == EdgeType.TWO_D:
            e = Edge2D(**item)
            e.pathType = DubinsPathType(item['pathType'])
            e.start = Vertex.from_dict(item['start'])
            e.end = Vertex.from_dict(item['end'])
            return e
        elif item['type'] == EdgeType.THREE_D:
            e = Edge3D(**item)
            e.pathType = DubinsPathType(item['pathType'])
            e.pathTypeSZ = DubinsPathType(item['pathTypeSZ'])
            e.start = Vertex.from_dict(item['start'])
            e.end = Vertex.from_dict(item['end'])
            return e
        elif item['type'] == EdgeType.DWELL_STRAIGHT:
            e = DwellStraightEdge(**item)
            e.start = Vertex.from_dict(item['start'])
            e.end = Vertex.from_dict(item['end'])
            e.dwellVector = np.array(e.dwellVector)
            e.transitionEdge = Edge.from_dict(e.transitionEdge)
            return e
        elif item['type'] == EdgeType.LEAD_IN_DWELL:
            e = LeadInDwellEdge(**item)
            e.start = Vertex.from_dict(item['start'])
            e.end = Vertex.from_dict(item['end'])
            e.dwellVector = np.array(e.dwellVector)
            e.leadVector = np.array(e.dwellVector)
            e.transitionEdge = Edge.from_dict(e.transitionEdge)
            return e
        else:
            return Edge(**item)


@dataclass
class Edge2D(Edge):
    start: Vertex2D
    end: Vertex2D
    aParam: float = 0
    bParam: float = 0
    cParam: float = 0
    pathType: DubinsPathType = DubinsPathType.UNKNOWN
    type: EdgeType = EdgeType.TWO_D
    radius: float = 0


@dataclass
class Edge3D(Edge2D):
    start: Vertex3D
    end: Vertex3D
    starParam: float = 0
    dParam: float = 0
    eParam: float = 0
    fParam: float = 0
    radiusSZ: float = 0
    pathTypeSZ: DubinsPathType = DubinsPathType.UNKNOWN
    type: EdgeType = EdgeType.THREE_D


@dataclass
class DwellStraightEdge(Edge):
    start: Vertex = field(default_factory=Vertex)
    end: Vertex = field(default_factory=Vertex)
    cost: float = 0
    dwellVector: 'list[float]' = field(default_factory=lambda: [0] * 3)
    transitionEdge: Edge = field(default_factory=Edge)
    type: EdgeType = EdgeType.DWELL_STRAIGHT


@dataclass
class LeadInDwellEdge(Edge):
    start: Vertex = field(default_factory=Vertex)
    end: Vertex = field(default_factory=Vertex)
    cost: float = 0
    dwellVector: 'list[float]' = field(default_factory=lambda: [0] * 3)
    leadVector: 'list[float]' = field(default_factory=lambda: [0] * 3)
    transitionEdge: Edge = field(default_factory=Edge)
    type: EdgeType = EdgeType.LEAD_IN_DWELL
