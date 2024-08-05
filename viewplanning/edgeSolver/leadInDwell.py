from .dwellStraight import DwellStraight
from .edgeSolver import EdgeSolver
from viewplanning.models import Vertex, Edge, VertexType, EdgeType, LeadInDwellEdge


class LeadInDwell(DwellStraight):
    '''
    an edge with a straight segment, a dubins path, and a straight segment
    '''
    def __init__(self, lead: float, dwell: float, edgeSolver: EdgeSolver, mulitplyDwell: bool):
        '''
        Parameters
        ----------
        lead: float
            lead distance
        dwell: float
            dwell distance
        edgeSolver: EdgeSolver
            calculates between vertices
        multiplyDwell: bool
            extend by the dwell by the number of vertices visited if True
        '''
        self.lead = lead
        super().__init__(dwell=dwell, edgeSolver=edgeSolver, multiplyDwell=mulitplyDwell)

    def getEdge(self, a: Vertex, b: Vertex) -> Edge:
        dwellMultiplier = len(a.visits) if (a.type == VertexType.THREE_D_MULTI or a.type == VertexType.TWO_D_MULTI) and self.multiplyDwell else 1
        dwellVector = self._getHeadingFromVertex(a)
        leadVector = self._getHeadingFromVertex(b)
        newEnd = self._getNewVertex(b, leadVector * -1 * self.lead)
        newStart = self._getNewVertex(a, dwellVector * self.dwell * dwellMultiplier)
        edge = self.edgeSolver.getEdge(newStart, newEnd)
        return LeadInDwellEdge(
            start=a,
            end=b,
            cost=self.dwell * dwellMultiplier + edge.cost + self.lead,
            dwellVector=dwellVector * self.dwell * dwellMultiplier,
            leadVector=leadVector * self.lead,
            transitionEdge=edge,
            type=EdgeType.LEAD_IN_DWELL
        )
