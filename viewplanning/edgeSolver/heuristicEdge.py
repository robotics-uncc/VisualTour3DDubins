from .edgeSolver import EdgeSolver
import numpy as np
from viewplanning.models import Vertex3D, Edge3D
from viewplanning.dubins import DubinsPath
from viewplanning.edgeSolver.etsp2dtsp import Etsp2Dtsp
from viewplanning.dubins.vanaAirplane import VanaAirplane


class HeuristicEdge(EdgeSolver):
    def __init__(self,
                 faMin: float,
                 faMax: float,
                 radius: float,
                 dubins: DubinsPath,
                 etsp2Dtsp: Etsp2Dtsp
                 ):
        self.faMax = faMax
        self.faMin = faMin
        self.radius = radius
        self.dubins = dubins
        self.etsp2Dtsp = etsp2Dtsp

    def edgeCost(self, a: Vertex3D, b: Vertex3D) -> float:
        x = a.asPoint()
        y = b.asPoint()
        dz = y[0, 2] - x[0, 2]
        hm = dz / np.sin(self.faMin)
        hp = dz / np.sin(self.faMax)
        h = abs(hm) if dz > 0 else abs(hp)
        cost = np.ceil(max(h, np.linalg.norm(x - y)))
        return cost

    def getEdge(self, a: Vertex3D, b: Vertex3D) -> Edge3D:
        p = VanaAirplane()
        path = p.calculatePath(a.x, a.y, a.z, a.theta, a.phi, b.x, b.y, b.z, b.theta, b.phi, self.radius, self.faMin, self.faMax)
        return self.dubins.calculatePath(a.x, a.y, a.z, a.theta, a.phi, b.x, b.y, b.z, b.theta, b.phi, self.radius, self.faMin, self.faMax)

    def getEdges(self, path: 'list[Vertex3D]'):
        self.etsp2Dtsp.findHeadings(path, self.faMin, self.faMax, self.radius)
        estimated = sum([self.edgeCost(path[i - 1], path[i]) for i in range(len(path))])
        edges = super().getEdges(path)
        actual = sum(map(lambda x: x.cost, edges))
        return edges
