from .dubinsHighAltitudeSolver import DubinsHighAltitudeSolver
from viewplanning.models import SolverType, Region, Environment
from .dubinsSolver import DubinsSolver
from viewplanning.sampling import SampleStrategy
from viewplanning.plotting import SolutionPlotter3dPyvista
from viewplanning.edgeSolver.etsp2dtsp import Etsp2Dtsp
from viewplanning.verification import VerificationStrategy
from viewplanning.dubins import DubinsPath
from viewplanning.tsp import MatrixTspSubprocess
from viewplanning.edgeSolver import DubinsAirplaneEdge, DubinsCarEdge, HeuristicEdge
from viewplanning.store import EnvironmentStore
import pyvista as pv
import uuid


class DubinsSolverBuilder(object):
    def __init__(self):
        self._sampleStrategy = None
        self._regions: 'list[Region]' = {}
        self._radius = 1
        self._tspFirst = False
        self._faBounds = 0
        self._type = SolverType.UNKNOWN
        self._etsp2Dtsp = Etsp2Dtsp()
        self._verification = VerificationStrategy()
        self._dubins = DubinsPath()
        self._environment: pv.PolyData = None
        self._numLevels: int = 2
        self._inflateRadius: float = 1
        self._sampleDistance: float = 10
        self.environmentStore = EnvironmentStore.getInstance()

    def addRegions(self, regions: list):
        self._regions = regions
        return self

    def setEnvironment(self, env: Environment):
        if env.file != '' and env.file is not None:
            self._environment = self.environmentStore.getEnvironment(env.file, env.rotationMatrix)
        self._numLevels = env.numLevels
        self._inflateRadius = env.inflateRadius
        self._sampleDistance = env.inflateRadius
        return self

    def setFlightAngleBounds(self, faBounds):
        self._faBounds = faBounds
        return self

    def setSampleStrategy(self, strategy: SampleStrategy):
        self._sampleStrategy = strategy
        return self

    def setRadius(self, radius):
        self._radius = radius
        return self

    def setSolverType(self, solverType: SolverType):
        self._type = solverType
        return self

    def setEtsp2Dtsp(self, etsp2Dtsp):
        self._etsp2Dtsp = etsp2Dtsp
        return self

    def setDubinsPath(self, dubins: DubinsPath):
        self._dubins = dubins
        return self

    def setVerificationStrategy(self, verification: VerificationStrategy):
        self._verification = verification
        return self

    def build(self) -> DubinsSolver:
        if self._type == SolverType.THREE_D_TSP_FIRST or self._type == SolverType.THREE_D_MODIFIED_DISTANCE:
            edgeSolver = HeuristicEdge(
                self._faBounds[0],
                self._faBounds[1],
                self._radius,
                self._dubins,
                self._etsp2Dtsp
            )
            return DubinsHighAltitudeSolver(
                self._regions,
                SolutionPlotter3dPyvista(self._environment),
                self._verification,
                self._sampleStrategy,
                edgeSolver,
                MatrixTspSubprocess(),
                uuid.uuid1()
            )
        elif self._type == SolverType.THREE_D:
            edgeSolver = DubinsAirplaneEdge(
                self._faBounds[0],
                self._faBounds[1],
                self._radius,
                self._dubins
            )
            return DubinsHighAltitudeSolver(
                self._regions,
                SolutionPlotter3dPyvista(self._environment),
                self._verification,
                self._sampleStrategy,
                edgeSolver,
                MatrixTspSubprocess(),
                uuid.uuid1()
            )
        elif self._type == SolverType.TWO_D:
            edgeSolver = DubinsCarEdge(
                self._radius,
                self._dubins
            )
            return DubinsHighAltitudeSolver(
                self._regions,
                SolutionPlotter3dPyvista(self._environment),
                self._verification,
                self._sampleStrategy,
                edgeSolver,
                MatrixTspSubprocess(),
                uuid.uuid1()
            )
        else:
            raise Exception('Unknown Solver Type {0}'.format(self._type))
