from .dubinsSolver import DubinsSolver
from viewplanning.sampling import SampleStrategy
from viewplanning.plotting import SolutionPlotter
from viewplanning.verification import VerificationStrategy
from viewplanning.models import Region, Edge
from viewplanning.tsp import TspSolver
from viewplanning.edgeSolver import EdgeSolver
import uuid


class DubinsHighAltitudeSolver(DubinsSolver):
    '''
    Solves the view planning problem aboce the urban environment.
    '''

    def __init__(self,
                 regions: 'list[Region]',
                 plotter: SolutionPlotter,
                 verification: VerificationStrategy,
                 sampleStrategy: SampleStrategy,
                 edgeSolver: EdgeSolver,
                 tspSolver: TspSolver,
                 id: uuid.UUID
                 ) -> None:
        '''
        Parameters
        ----------
        regions: list[Region]
            list of regeions where the aircraft can view the target
        plotter: SolutionPlotter
            plotter that will visualize the solution
        verification: VerificationStrategy
            method for verifying that the solution can view all of the targets
        sampleStrategy: SampleStrategy
            method for sampling the regions for configurations
        edgeSolver: EdgeSolver
            method for computing paths between configurations
        tspSolver: TspSolver
            traveling salesperson problem solving method
        id: UUID
            id of solver for disallowing collision of temporary files
        '''
        super().__init__(regions, plotter, verification, sampleStrategy, edgeSolver, tspSolver, id)

    def solve(self) -> 'list[Edge]':
        vertices = self.sample()

        def costFunction(x, y):
            return self.edgeSolver.edgeCost(x, y)
        try:
            self.tspSolver.writeFiles(self.id, vertices, costFunction)
            path = self.tspSolver.solve(self.id, vertices)
            edges = self.edgeSolver.getEdges(path)
            return edges
        except Exception as e:
            raise e
        finally:
            self.tspSolver.cleanUp(self.id)
