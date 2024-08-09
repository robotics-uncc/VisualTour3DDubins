import uuid
from viewplanning.models import Edge, Region
from viewplanning.sampling import SampleStrategy, SamplingFailedException
from viewplanning.tsp.Tsp import TspSolver
from viewplanning.verification import VerificationStrategy
from viewplanning.plotting import SolutionPlotter
from viewplanning.edgeSolver import EdgeSolver
from uuid import UUID


class DubinsSolver(object):
    '''
    abstract class for solving the viewplanning problem
    '''
    def __init__(self,
                 regions: 'list[Region]',
                 plotter: SolutionPlotter,
                 verification: VerificationStrategy,
                 sampleStrategy: SampleStrategy,
                 edgeSolver: EdgeSolver,
                 tspSolver: TspSolver,
                 id: UUID
                 ):
        self.plotter = plotter
        self.verificationStrategy = verification
        self.edges: 'list[Edge]' = []
        self.regions = regions
        self.sampleStrategy = sampleStrategy
        self.edgeSolver = edgeSolver
        self.tspSolver = tspSolver
        self.vertices = []
        self.id = id

    def sample(self):
        samples = self.sampleStrategy.getSamples(self.regions)
        self.vertices = samples
        # check for sampling success
        groups = set()
        for vertex in self.vertices:
            if int(vertex.group) not in groups:
                groups.add(int(vertex.group))
        if len(groups) != len(self.regions):
            real = set(range(len(self.regions)))
            diff = real.difference(groups)
            names = [self.regions[j].file for j in diff]
            raise SamplingFailedException(f'Sampling failed {type(self.sampleStrategy).__name__} couldn\'t sample regions {names}')

        return samples

    def solve(self) -> 'list[Edge]':
        '''
        Solve the view planning problem

        Returns
        -------
        list[Edge]
            solution to the view planning problem
        '''
        pass

    def verify(self) -> int:
        '''
        Verify the view planning solution is valid
        '''
        return True

    def plot(self):
        '''
        Plot the soluiton to the view planning problem
        '''
        self.plotter.plot(self.regions, self.edges)

    def cleanUp(self):
        '''
        Cleanup temporary resources after solving the problem
        '''
        self.tspSolver.cleanUp(self.id)
