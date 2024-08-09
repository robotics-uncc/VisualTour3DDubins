from .dubinsHighAltitudeSolver import DubinsHighAltitudeSolver
from viewplanning.models import SolverType, Region, Environment
from .dubinsSolver import DubinsSolver
from viewplanning.sampling import SampleStrategy
from viewplanning.plotting import SolutionPlotter3dPyvista, SolutionPlotter2dRegions
from viewplanning.edgeSolver.etsp2dtsp import Etsp2Dtsp
from viewplanning.verification import VerificationStrategy
from viewplanning.dubins import DubinsPath
from viewplanning.tsp import MatrixTspSubprocess
from viewplanning.edgeSolver import DubinsAirplaneEdge, DubinsCarEdge, HeuristicEdge
from viewplanning.store import MeshStore
from viewplanning.tsp import TspSolver
from viewplanning.edgeSolver import EdgeSolver
import pyvista as pv
import uuid


class DubinsSolverBuilder(object):
    def __init__(self):
        self._sampleStrategy = None
        self._regions: 'list[Region]' = {}
        self._type = SolverType.UNKNOWN
        self._verification = VerificationStrategy()
        self._environment: pv.PolyData = None
        self._numLevels: int = 2
        self._inflateRadius: float = 1
        self._sampleDistance: float = 10
        self._tspSolver: TspSolver = MatrixTspSubprocess()
        self._edgeSolver: EdgeSolver = None
        self.environmentStore = MeshStore.getInstance()
        self._id: uuid.UUID = uuid.uuid1()

    def addRegions(self, regions: list):
        self._regions = regions
        return self
    
    def setId(self, id: uuid.UUID):
        self._id = id
        return self

    def setEnvironment(self, env: Environment):
        if env.file != '' and env.file is not None:
            self._environment = self.environmentStore.getMesh(env.file, env.rotationMatrix)
        self._numLevels = env.numLevels
        self._inflateRadius = env.inflateRadius
        self._sampleDistance = env.inflateRadius
        return self

    def setSampleStrategy(self, strategy: SampleStrategy):
        self._sampleStrategy = strategy
        return self

    def setSolverType(self, solverType: SolverType):
        self._type = solverType
        return self

    def setVerificationStrategy(self, verification: VerificationStrategy):
        self._verification = verification
        return self

    def setTSPSolver(self, tsp):
        self._tspSolver = tsp
        return self

    def setEdgeSolver(self, edgeSolver: EdgeSolver):
        self._edgeSolver = edgeSolver
        return self

    def build(self) -> DubinsSolver:
        if self._type == SolverType.HIGH_ALTITUDE:
            return DubinsHighAltitudeSolver(
                self._regions,
                SolutionPlotter3dPyvista(self._environment),
                self._verification,
                self._sampleStrategy,
                self._edgeSolver,
                self._tspSolver,
                self._id
            )
        else:
            raise Exception('Unknown Solver Type {0}'.format(self._type))
