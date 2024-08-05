from .edgeSolver import EdgeSolver
from viewplanning.models import Vertex, Edge, VertexType, Vertex2D, Vertex3D, DwellStraightEdge, EdgeType
import numpy as np
import copy


class DwellStraight(EdgeSolver):
    '''
    a curve with a straight line segment then a dubins curve
    '''
    def __init__(self, dwell: float, edgeSolver: EdgeSolver, multiplyDwell: bool):
        '''
        Parameters
        ----------
        dwell: float
            length of straight segment
        
        edgeSolver: EdgeSolver
            calculates curve to next vertex
        
        multiplyDwell: bool
            extends dwell by the number of neighborhoods visited if True
        '''
        self.dwell = dwell
        self.edgeSolver = edgeSolver
        self.multiplyDwell = multiplyDwell

    def getEdge(self, a: Vertex, b: Vertex) -> Edge:
        dwellMultiplier = len(a.visits) if (a.type == VertexType.THREE_D_MULTI or a.type == VertexType.TWO_D_MULTI) and self.multiplyDwell else 1
        dwellVector = self._getHeadingFromVertex(a)
        newStart = self._getNewVertex(a, dwellVector * self.dwell * dwellMultiplier)
        edge = self.edgeSolver.getEdge(newStart, b)
        return DwellStraightEdge(
            start=a,
            end=b,
            cost=self.dwell * dwellMultiplier + edge.cost,
            dwellVector=dwellVector * self.dwell * dwellMultiplier,
            transitionEdge=edge
        )

    def _getHeadingFromVertex(self, vec: Vertex) -> np.ndarray:
        if vec.type == VertexType.TWO_D or vec.type == VertexType.TWO_D_MULTI:
            v: Vertex2D = vec
            return np.array([np.cos(v.theta), np.sin(v.theta)])
        elif vec.type == VertexType.THREE_D or vec.type == VertexType.THREE_D_MULTI:
            v: Vertex3D = vec
            return np.array([np.cos(v.theta) * np.cos(v.phi), np.sin(v.theta) * np.cos(v.phi), np.sin(v.phi)])

    def _getNewVertex(self, vec: Vertex, offset: np.ndarray) -> Vertex:
        if vec.type == VertexType.TWO_D or vec.type == VertexType.TWO_D_MULTI:
            v: Vertex2D = copy.deepcopy(vec)
            v.x += offset[0]
            v.y += offset[1]
            return v
        elif vec.type == VertexType.THREE_D or vec.type == VertexType.THREE_D_MULTI:
            v: Vertex3D = copy.deepcopy(vec)
            v.x += offset[0]
            v.y += offset[1]
            v.z += offset[2]
            return v
