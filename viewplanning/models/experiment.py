from dataclasses import dataclass, field
from .environment import Environment, RoadMapType
from .region import Region, RegionType
from .sampleStrategyRecord import SampleStrategyRecord, SampleStrategyType, HeadingStrategyRecord, HeadingStrategyType, IntersectionStrategyRecord, SampleStrategyIntersection
from .solverType import SolverType
from .etsp2dtspType import Etsp2DtspType
from .verificationType import VerificationType
from .edgeStrategyRecord import EdgeStrategyRecord, EdgeModification, EdgeStrategyType
import uuid
import numpy as np


@dataclass
class Experiment(object):
    edgeStrategy: EdgeStrategyRecord = field(
        default_factory=EdgeStrategyRecord),
    solverType: SolverType = SolverType.UNKNOWN
    verificationType: VerificationType = VerificationType.DEFAULT
    sampleStrategy: SampleStrategyRecord = field(
        default_factory=SampleStrategyRecord)
    group: str = field(default_factory=str)
    _id: uuid.UUID = field(default_factory=uuid.uuid1)
    regions: 'list[Region]' = field(default_factory=list)
    environment: Environment = field(default_factory=Environment)

    @staticmethod
    def from_dict(item: dict):
        n = Experiment(
            group=item.get('group', ''),
            solverType=item.get('solverType', SolverType.UNKNOWN),
            verificationType=item.get(
                'verificationType', VerificationType.DEFAULT),
            _id=item.get('_id', uuid.UUID(
                '00000000-0000-0000-0000-000000000000')),
        )
        if 'edgeStrategy' in item.keys():
            n.edgeStrategy = EdgeStrategyRecord(**item['edgeStrategy'])
        else:
            # old experiment compatibility
            solver = item.get('solverType', 0)
            modification = EdgeModification.NONE
            edgeSolver = EdgeStrategyType.UNKNOWN
            if solver == SolverType.THREE_D:
                solver = SolverType.HIGH_ALTITUDE
                edgeSolver = EdgeStrategyType.VANA_AIRPLANE
            elif solver == SolverType.THREE_D_MODIFIED_DISTANCE or solver == SolverType.THREE_D_TSP_FIRST:
                solver = SolverType.HIGH_ALTITUDE
                edgeSolver = EdgeStrategyType.MODIFIED_AIRPLANE
            elif solver == SolverType.TWO_D:
                solver = SolverType.HIGH_ALTITUDE
                edgeSolver = edgeSolver.DUBINS_CAR
            else:
                raise Exception('Error Parsing Experiment')

            n.solverType = solver

            n.edgeStrategy = EdgeStrategyRecord(
                dwellDistance=0,
                leadDistance=0,
                etsp2DTSPType=item.get('estp2dtspType', Etsp2DtspType.UNKNOWN),
                radius=item.get('radius', 1),
                flightAngleBounds=item.get('flightAngleBounds', [0] * 2),
                type=edgeSolver,
                modification=modification)

        n.sampleStrategy = SampleStrategyRecord.from_dict(
            item['sampleStrategy'])
        n.regions = [Region(**r) for r in item['regions']]
        if 'environment' in item.keys():
            n.environment = Environment(**item['environment'])
        return n


def makeExperiment(
    solverType=SolverType.HIGH_ALTITUDE,
    sampleType=SampleStrategyType.FACE,
    numPhi=1,
    numTheta=1,
    numSamples=1,
    regions: 'list[Region]' = None,
    radius=1,
    faBounds=[0, 0],
    phiRange=[0, 0],
    regionType=RegionType.WAVEFRONT,
    etsp2Dtsp=Etsp2DtspType.UNKNOWN,
    group: str = '',
    hyperparameters: 'list[float]' = [],
    verificationType: VerificationType = VerificationType.DEFAULT,
    envFile: str = '',
    beta: float = 0,
    var: float = 0,
    roadMapType: RoadMapType = RoadMapType.UNKNOWN,
    inflateRadius: float = 1.0,
    sampleDistance: float = 1.0,
    numLevels: int = 2,
    envRotMatrix: 'list[list[float]]' = None,
    dwellDistance: float = 0,
    leadDistance: float = 0,
    edgeType: EdgeStrategyType = EdgeStrategyType.VANA_AIRPLANE,
    modification: EdgeModification = EdgeModification.NONE,
    headingStrategyType: HeadingStrategyType = HeadingStrategyType.UNKNOWN,
    numRays: int = 64,
    intersectionType: SampleStrategyIntersection = SampleStrategyIntersection.NON_INTERSECTING,
    cliqueLimit: int = 3,
    intersectionRadius: float = 300,
    intersectionAlpha: float = 1,
    multiplyDwell: bool = True
):
    if envRotMatrix is None:
        envRotMatrix = np.eye(3).tolist()

    regions = [] if regions is None else regions
    for region in regions:
        region.type = regionType

    return Experiment(
        regions=regions,
        sampleStrategy=SampleStrategyRecord(
            type=sampleType,
            numSamples=numSamples,
            numTheta=numTheta,
            numPhi=numPhi,
            phiRange=phiRange,
            hyperParameters=hyperparameters,
            heading=HeadingStrategyRecord(
                type=headingStrategyType,
                headingRange=[0, np.pi * 2],
                dwellDistance=dwellDistance,
                numRays=numRays,
                multiplyDwell=multiplyDwell
            ),
            intersection=IntersectionStrategyRecord(
                type=intersectionType,
                cliqueLimit=cliqueLimit,
                alpha=intersectionAlpha,
                cliqueRadius=intersectionRadius
            )
        ),
        edgeStrategy=EdgeStrategyRecord(
            dwellDistance=dwellDistance,
            leadDistance=leadDistance,
            flightAngleBounds=faBounds,
            etsp2DTSPType=etsp2Dtsp,
            radius=radius,
            type=edgeType,
            modification=modification),
        solverType=solverType,
        group=group,
        environment=Environment(
            file=envFile,
            sampleDistance=sampleDistance,
            inflateRadius=inflateRadius,
            numLevels=numLevels,
            beta=beta,
            var=var,
            roadMapType=roadMapType,
            rotationMatrix=envRotMatrix
        ),
        verificationType=verificationType
    )
