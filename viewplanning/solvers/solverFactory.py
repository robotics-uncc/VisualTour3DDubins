from viewplanning.dubins import RustVanaAirplane, RustDubinsCar
from viewplanning.verification import VerificationStrategy, PathVerification, StartPointVerification
from viewplanning.edgeSolver.etsp2dtsp import Etsp2Dtsp, Alternating, AlternatingBisector, AngleBisector
from viewplanning.models import Experiment, SampleStrategyType, SolverType, Etsp2DtspType, VerificationType
from viewplanning.models.sampleStrategyRecord import SampleStrategyRecord
from viewplanning.solvers.dubinsSolverBuilder import DubinsSolverBuilder
from viewplanning.sampling import BodySampleStrategy, PointSampleStrategy, FaceSampleStrategy, \
    PerimeterWeightedFaceSampleStrategy, GlobalPerimeterWeightedFaceSampleStrategy, \
    MaxAreaEdgeSampleStrategy, Edge3dSampleStrategy, MaxAreaPolygonSampleStrategy


def makeSolver(experiment: Experiment):
    builder = DubinsSolverBuilder()

    return builder.setRadius(experiment.radius) \
        .setSolverType(experiment.solverType) \
        .setFlightAngleBounds(experiment.flightAngleBounds) \
        .setSampleStrategy(makeStrategy(experiment.sampleStrategy)) \
        .addRegions(experiment.regions) \
        .setEtsp2Dtsp(makeEtsp2Dtsp(experiment.etsp2DtspType)) \
        .setVerificationStrategy(makeVerificationStrategy(experiment.verificationType)) \
        .setDubinsPath(makeDubins(experiment.solverType)) \
        .setEnvironment(experiment.environment) \
        .build()


def makeStrategy(sample: SampleStrategyRecord):
    if sample.type == SampleStrategyType.BODY:
        return BodySampleStrategy(sample.numSamples, sample.numTheta, sample.numPhi, sample.phiRange)
    elif sample.type == SampleStrategyType.POINT:
        return PointSampleStrategy(sample.numTheta)
    elif sample.type == SampleStrategyType.FACE:
        return FaceSampleStrategy(sample.numSamples, sample.numTheta, sample.numPhi, sample.phiRange)
    elif sample.type == SampleStrategyType.WEIGHTED_FACE:
        return PerimeterWeightedFaceSampleStrategy(sample.numSamples, sample.numTheta, sample.numPhi, sample.phiRange)
    elif sample.type == SampleStrategyType.GLOBAL_WEIGHTED_FACE:
        return GlobalPerimeterWeightedFaceSampleStrategy(sample.numSamples, sample.numTheta, sample.numPhi,
                                                         sample.phiRange, *sample.hyperParameters)
    elif sample.type == SampleStrategyType.MAX_AREA_EDGE:
        return MaxAreaEdgeSampleStrategy(sample.numSamples, sample.numTheta)
    elif sample.type == SampleStrategyType.EDGE_3D:
        return Edge3dSampleStrategy(sample.numSamples, sample.numTheta, sample.numPhi, sample.phiRange)
    elif sample.type == SampleStrategyType.MAX_AREA_POLYGON:
        return MaxAreaPolygonSampleStrategy(sample.numSamples, sample.numTheta)
    else:
        raise Exception('Unknown Sampling Type {0}'.format(sample.type))


def makeEtsp2Dtsp(type: Etsp2DtspType):
    if type == Etsp2DtspType.UNKNOWN:
        return Etsp2Dtsp()
    elif type == Etsp2DtspType.ALTERNATING:
        return Alternating()
    elif type == Etsp2DtspType.ALTERNATING_BISECTOR:
        return AlternatingBisector()
    elif type == Etsp2DtspType.BISECTOR:
        return AngleBisector()


def makeVerificationStrategy(type: VerificationType):
    if type == VerificationType.DEFAULT:
        return VerificationStrategy()
    elif type == VerificationType.START_POINT:
        return StartPointVerification()
    elif type == VerificationType.PATH:
        return PathVerification()


def makeDubins(type: SolverType):
    if type == SolverType.THREE_D or type == SolverType.THREE_D_MODIFIED_DISTANCE \
            or type == SolverType.THREE_D_TSP_FIRST:
        return RustVanaAirplane()
    elif type == SolverType.TWO_D:
        return RustDubinsCar()
    else:
        return None
