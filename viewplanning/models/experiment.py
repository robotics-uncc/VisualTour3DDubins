from dataclasses import dataclass, field
from .environment import Environment, RoadMapType
from .region import Region, RegionType
from .sampleStrategyRecord import SampleStrategyRecord, SampleStrategyType
from .solverType import SolverType
from .etsp2dtspType import Etsp2DtspType
from .verificationType import VerificationType
import uuid
import numpy as np


@dataclass
class Experiment(object):
    radius: float = 1
    flightAngleBounds: 'list[float]' = field(default_factory=list)
    dubinsCost: object = None,
    solverType: SolverType = SolverType.UNKNOWN
    etsp2DtspType: Etsp2DtspType = Etsp2DtspType.UNKNOWN
    verificationType: VerificationType = VerificationType.DEFAULT
    sampleStrategy: SampleStrategyRecord = field(default_factory=SampleStrategyRecord)
    group: str = field(default_factory=str)
    _id: uuid.UUID = field(default_factory=uuid.uuid1)
    regions: 'list[Region]' = field(default_factory=list)
    environment: Environment = field(default_factory=Environment)
    beta: float = 0
    var: float = 0

    @staticmethod
    def from_dict(item: dict):
        n = Experiment(**item)
        n.sampleStrategy = SampleStrategyRecord(**item['sampleStrategy'])
        n.regions = [Region(**r) for r in item['regions']]
        n.radius = float(n.radius)
        if 'environment' in item.keys():
            n.environment = Environment(**item['environment'])
        return n


def makeExperiment(
    solverType=SolverType.THREE_D,
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
    envRotMatrix: 'list[list[float]]' = None
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
            hyperParameters=hyperparameters
        ),
        radius=radius,
        flightAngleBounds=faBounds,
        solverType=solverType,
        etsp2DtspType=etsp2Dtsp,
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
