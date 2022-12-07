from viewplanning.models.edge import Edge2D
from .edgeSolver import EdgeSolver
from viewplanning.dubins import DubinsPath
from viewplanning.models import Vertex2D
import numpy as np


class DubinsCarEdge(EdgeSolver):
    def __init__(self,
        radius: float,
        dubins: DubinsPath
    ):
        self.dubins = dubins
        self.radius = radius
    
    def getEdge(self, a: Vertex2D, b: Vertex2D) -> Edge2D:
        return self.dubins.calculatePath(a.x, a.y, a.theta, b.x, b.y, b.theta, self.radius)
