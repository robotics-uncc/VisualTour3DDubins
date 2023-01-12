from viewplanning.models import Vertex, Edge
import numpy as np


class EdgeSolver:
    '''super class for creating edges'''

    def edgeCost(self, a: Vertex, b: Vertex) -> float:
        '''
        get the edge cost from a to b

        Parameters
        ----------
        a: Vertex
            starting position
        b: Vertex
            ending position

        Returns
        -------
        float
            cost of path from a to b
        '''
        edge = self.getEdge(a, b)
        if edge is None:
            return np.inf
        return edge.cost

    def getEdge(self, a: Vertex, b: Vertex) -> Edge:
        '''
        creates and edge from a to b

        Parameters
        ----------
        a: Vertex
            starting position
        b: Vertex
            ending position

        Returns
        -------
        Edge
            edge from a to b
        '''
        return None

    def getEdges(self, path: 'list[Vertex]') -> 'list[Edge]':
        '''
        creates the edges for the cycle

        Parameters
        ----------
        path: list[Vertex]
            cycle of vertices

        Returns
        -------
        list[Edge]
            cycle of edges
        '''
        return [self.getEdge(path[i - 1], path[i]) for i in range(len(path))]
