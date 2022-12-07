from viewplanning.models import Vertex, Edge
import numpy as np


class EdgeSolver:
    def edgeCost(self, a: Vertex, b: Vertex) -> float:
        edge = self.getEdge(a, b)
        if edge is None:
            return np.inf
        return edge.cost
    
    def getEdge(self, a: Vertex, b: Vertex) -> Edge:
        return None
    
    def getEdges(self, path: 'list[Vertex]') -> 'list[Edge]':
        return [self.getEdge(path[i - 1], path[i]) for i in range(len(path))]
        