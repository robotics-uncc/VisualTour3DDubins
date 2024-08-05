import numpy as np
from enum import IntEnum
from dataclasses import dataclass, field


class VertexType(IntEnum):
    UNKNOWN = 0
    TWO_D = 1
    THREE_D = 2
    TWO_D_MULTI = 3
    THREE_D_MULTI = 4


@dataclass
class Vertex(object):
    group: str = field(default_factory=str)
    type: VertexType = VertexType.UNKNOWN

    def asPoint(self):
        return np.zeros([0, 0])

    def toList(self):
        return []

    @staticmethod
    def from_dict(item: dict):
        if item['type'] == VertexType.TWO_D:
            return Vertex2D(**item)
        elif item['type'] == VertexType.THREE_D:
            return Vertex3D(**item)
        elif item['type'] == VertexType.TWO_D_MULTI:
            return Vertex2DMulti.from_dict(item)
        elif item['type'] == VertexType.THREE_D_MULTI:
            return Vertex3DMulti.from_dict(item)
        else:
            return Vertex(**item)


@dataclass
class Vertex2D(Vertex):
    x: float = 0
    y: float = 0
    theta: float = 0
    type: VertexType = VertexType.TWO_D

    def asPoint(self):
        return np.array([[self.x, self.y]])

    def toList(self):
        return [self.x, self.y, self.theta]


@dataclass
class Vertex3D(Vertex2D):
    z: float = 0
    phi: float = 0
    type: VertexType = VertexType.THREE_D

    def asPoint(self):
        return np.array([[self.x, self.y, self.z]])

    def toList(self):
        return [self.x, self.y, self.z, self.theta, self.phi]


@dataclass
class VertexMulti(Vertex):
    id: int = -1
    group: int = -1
    type: VertexType = VertexType.UNKNOWN
    visits: 'set[int]' = field(default_factory=set)


@dataclass
class Vertex2DMulti(VertexMulti):
    x: float = 0
    y: float = 0
    theta: float = 0
    type: VertexType = VertexType.TWO_D_MULTI

    def asPoint(self):
        return np.array([[self.x, self.y]])

    def toList(self):
        return [self.x, self.y, self.theta]

    @staticmethod
    def from_dict(item: dict):
        obj = Vertex2DMulti(**item)
        obj.visits = set(obj.visits)
        return obj


@dataclass
class Vertex3DMulti(Vertex2DMulti):
    z: float = 0
    phi: float = 0
    type: VertexType = VertexType.THREE_D_MULTI

    def asPoint(self):
        return np.array([[self.x, self.y, self.z]])

    def toList(self):
        return [self.x, self.y, self.z, self.theta, self.phi]

    @staticmethod
    def from_dict(item: dict):
        obj = Vertex3DMulti(**item)
        obj.visits = set(obj.visits)
        return obj
