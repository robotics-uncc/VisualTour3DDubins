from viewplanning.models import Experiment, SampleStrategyType, Etsp2DtspType, VerificationType, SampleStrategyIntersection, SampleStrategyRecord, HeadingStrategyType, EdgeStrategyType, EdgeStrategyRecord, EdgeModification
from viewplanning.solvers.dubinsSolverBuilder import DubinsSolverBuilder
from viewplanning.sampling.single import BodySampleStrategy, PointSampleStrategy, FaceSampleStrategy, GlobalPerimeterWeightedFaceSampleStrategy, MaxAreaEdgeSampleStrategy, MaxAreaPolygonSampleStrategy, Edge3dSampleStrategy
from viewplanning.sampling.multi import IntersectingFaceSampling, IntersectingEdge3DSampling, IntersectingGlobalWeightedFaceSampling, IntersectingMaxAreaEdgeSampling, SimpleIntersectingVolumeSampling, BruteVolumeSampling
from viewplanning.sampling.heading import UniformHeadings, InwardPointingHeadings, StraightDwellHeadings
from viewplanning.edgeSolver.etsp2dtsp import Etsp2Dtsp, Alternating, AlternatingBisector, AngleBisector
from viewplanning.verification import VerificationStrategy, PathVerification, StartPointVerification
from viewplanning.dubins import RustVanaAirplane, RustDubinsCar
from viewplanning.edgeSolver import DubinsAirplaneEdge, DubinsCarEdge, DwellStraight, HeuristicEdge, LeadInDwell
from viewplanning.tsp import OverlappingTspSubprocess
from math import pi
import logging


def makeSolver(experiment: Experiment):
    '''
    factory method for making view planning problem solvers

    Parameters
    ----------
    experiment: Experiment
        experiment to solve
    '''
    builder = DubinsSolverBuilder()

    builder.setSolverType(experiment.solverType) \
        .setSampleStrategy(makeStrategy(experiment.sampleStrategy)) \
        .addRegions(experiment.regions) \
        .setVerificationStrategy(makeVerificationStrategy(experiment.verificationType)) \
        .setEnvironment(experiment.environment) \
        .setEdgeSolver(makeEdgeSolver(experiment.edgeStrategy, experiment.sampleStrategy)) \
        .setId(experiment._id)

    if (experiment.sampleStrategy.intersection.type == SampleStrategyIntersection.SIMPLE_INTERSECTION
            or experiment.sampleStrategy.intersection.type == SampleStrategyIntersection.BRUTE_INTERSECTION):
        builder.setTSPSolver(OverlappingTspSubprocess())

    return builder.build()


def makeStrategy(sample: SampleStrategyRecord):
    '''
    factory method for creating a sample strategy

    Parameters
    ----------
    sample: SampleStrategyRecord
        sample strategy to create
    '''
    if sample.intersection.type == SampleStrategyIntersection.NON_INTERSECTING:
        return makeStrategySingle(sample)
    elif sample.intersection.type == SampleStrategyIntersection.SIMPLE_INTERSECTION:
        method = makeStrategyMulti(sample)
        return SimpleIntersectingVolumeSampling(method)
    elif sample.intersection.type == SampleStrategyIntersection.BRUTE_INTERSECTION:
        method = makeStrategyMulti(sample)
        return BruteVolumeSampling(method, sample.intersection.cliqueRadius, sample.intersection.cliqueLimit)
    elif sample.intersection.type == SampleStrategyIntersection.UNKNOWN:
        raise Exception(
            'Unknown Sampling Intersection Type {0}'.format(sample.intersection))


def makeStrategyMulti(sample: SampleStrategyRecord):
    '''
        factory method for making a sample strategy that considers the intersection of visibility volumes.

    Parameters
    ----------
    sample: SampleStrategyRecord
        sample strategy to create
    '''
    heading = makeHeadingStrategy(sample)
    if sample.type == SampleStrategyType.FACE:
        return IntersectingFaceSampling(sample.numSamples, sample.numPhi, sample.phiRange, heading)
    elif sample.type == SampleStrategyType.GLOBAL_WEIGHTED_FACE:
        return IntersectingGlobalWeightedFaceSampling(sample.numSamples, sample.numPhi, sample.phiRange, sample.hyperParameters[0], heading)
    elif sample.type == SampleStrategyType.MAX_AREA_EDGE:
        return IntersectingMaxAreaEdgeSampling(sample.numSamples, heading)
    elif sample.type == SampleStrategyType.EDGE_3D:
        return IntersectingEdge3DSampling(sample.numSamples, sample.numPhi, sample.phiRange, heading)
    else:
        raise Exception('Unknown Sampling Type {0}'.format(sample.type))


def makeStrategySingle(sample: SampleStrategyRecord):
    '''
        factory method for making a sample strategy that does not consider the intersection of visibility volumes.

    Parameters
    ----------
    sample: SampleStrategyRecord
        sample strategy to create
    '''
    heading = makeHeadingStrategy(sample)
    if sample.type == SampleStrategyType.BODY:
        return BodySampleStrategy(sample.numSamples, sample.numPhi, sample.phiRange, heading)
    elif sample.type == SampleStrategyType.POINT:
        return PointSampleStrategy(heading)
    elif sample.type == SampleStrategyType.FACE:
        return FaceSampleStrategy(sample.numSamples, sample.numPhi, sample.phiRange, heading)
    elif sample.type == SampleStrategyType.GLOBAL_WEIGHTED_FACE:
        return GlobalPerimeterWeightedFaceSampleStrategy(sample.numSamples, sample.numPhi, sample.phiRange, sample.hyperParameters[0], heading)
    elif sample.type == SampleStrategyType.MAX_AREA_EDGE:
        return MaxAreaEdgeSampleStrategy(sample.numSamples, heading)
    elif sample.type == SampleStrategyType.MAX_AREA_POLYGON:
        return MaxAreaPolygonSampleStrategy(sample.numSamples, heading)
    elif sample.type == SampleStrategyType.EDGE_3D:
        return Edge3dSampleStrategy(sample.numSamples, sample.numPhi, sample.phiRange, heading)
    else:
        raise Exception('Unknown Sampling Type {0}'.format(sample.type))


def makeHeadingStrategy(sample: SampleStrategyRecord):
    '''
        factory method for making a method to sample heading for visilibity volume samples

    Parameters
    ----------
    sample: SampleStartegyRecord
        sample strategy to create
    '''
    if sample.heading.type == HeadingStrategyType.UNIFORM:
        return UniformHeadings(sample.numTheta, sample.heading.headingRange)
    elif sample.heading.type == HeadingStrategyType.INWARD:
        return InwardPointingHeadings(sample.numTheta)
    elif sample.heading.type == HeadingStrategyType.DWELL:
        return StraightDwellHeadings(sample.numTheta, sample.heading.numRays, sample.heading.dwellDistance, multiplyDwell=sample.heading.multiplyDwell)

    logging.warn(
        "sample strategy doesn't contain heading strategy using backwards compatibility")
    # backwards compatibility
    if sample.type == SampleStrategyType.BODY or sample.type == SampleStrategyType.POINT:
        return UniformHeadings(sample.numTheta, [0, 2 * pi])
    else:
        return InwardPointingHeadings(sample.numTheta)


def makeEtsp2Dtsp(type: Etsp2DtspType):
    '''
    factory method for creating method to convert 3D ETSP to a 3D DTSP

    Parameters
    ----------
    type; Etsp2DtspType
        enum for selecting method
    '''
    if type == Etsp2DtspType.UNKNOWN:
        return Etsp2Dtsp()
    elif type == Etsp2DtspType.ALTERNATING:
        return Alternating()
    elif type == Etsp2DtspType.ALTERNATING_BISECTOR:
        return AlternatingBisector()
    elif type == Etsp2DtspType.BISECTOR:
        return AngleBisector()


def makeVerificationStrategy(type: VerificationType):
    '''
    factory method for verification method of resulting path 

    Parameters
    ----------
    type: VerificationType
        enum for selection method
    '''
    if type == VerificationType.DEFAULT:
        return VerificationStrategy()
    elif type == VerificationType.START_POINT:
        return StartPointVerification()
    elif type == VerificationType.PATH:
        return PathVerification()


def makeEdgeSolver(edgeRecord: EdgeStrategyRecord, sampleRecord: SampleStrategyRecord):
    '''
    create the method to make edges between sampled vertices

    Parameters
    ----------
    edgeRecord: EdgeStrategyRecord
        which edge strategy to use
    sampleRecord: SampleStrategyRecord
        how the vertices will be sampled
    '''
    if edgeRecord.type == EdgeStrategyType.DUBINS_CAR:
        edge = DubinsCarEdge(
            edgeRecord.radius,
            RustDubinsCar()
        )
    elif edgeRecord.type == EdgeStrategyType.VANA_AIRPLANE:
        edge = DubinsAirplaneEdge(
            edgeRecord.flightAngleBounds[0],
            edgeRecord.flightAngleBounds[1],
            edgeRecord.radius,
            RustVanaAirplane()
        )
    elif edgeRecord.type == EdgeStrategyType.MODIFIED_AIRPLANE:
        edge = HeuristicEdge(
            edgeRecord.flightAngleBounds[0],
            edgeRecord.flightAngleBounds[1],
            edgeRecord.radius,
            RustVanaAirplane(),
            makeEtsp2Dtsp(edgeRecord.etsp2DTSPType)
        )

    if edgeRecord.modification == EdgeModification.DWELL:
        edge = DwellStraight(edgeRecord.dwellDistance, edge,
                             sampleRecord.heading.multiplyDwell)
    if edgeRecord.modification == EdgeModification.LEAD_IN_DWELL:
        edge = LeadInDwell(edgeRecord.leadDistance, edgeRecord.dwellDistance,
                           edge, sampleRecord.heading.multiplyDwell)
    return edge
