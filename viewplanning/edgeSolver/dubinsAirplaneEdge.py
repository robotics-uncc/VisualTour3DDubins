from viewplanning.dubins import DubinsPath
from .edgeSolver import EdgeSolver
from viewplanning.models import Vertex3D, Edge3D


class DubinsAirplaneEdge(EdgeSolver):
    '''
        find Dubins airplane edge
    '''

    def __init__(self,
                 faMin: float,
                 faMax: float,
                 radius: float,
                 dubins: DubinsPath
                 ):
        self.dubins = dubins
        self.faMin = faMin
        self.faMax = faMax
        self.radius = radius

    def getEdge(self, a: Vertex3D, b: Vertex3D) -> Edge3D:
        return self.dubins.calculatePath(
            a.x,
            a.y,
            a.z,
            a.theta,
            a.phi,
            b.x,
            b.y,
            b.z,
            b.theta,
            b.phi,
            self.radius,
            self.faMin,
            self.faMax
        )
