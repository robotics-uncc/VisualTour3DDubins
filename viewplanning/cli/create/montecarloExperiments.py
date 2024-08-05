import numpy as np
from viewplanning.models import SolverType, RegionType, RegionGroup, SampleStrategyType, Experiment, Etsp2DtspType, makeExperiment, EdgeModification, HeadingStrategyType, EdgeStrategyType, SampleStrategyIntersection
from viewplanning.store import CollectionStoreFactory
from viewplanning.cli.subapplication import Subapplication
from argparse import ArgumentParser, FileType
import json
from uuid import UUID

class MonteCarloExperiments(Subapplication):
    '''
    creates a monte caro expeirment from a group of view volumes
    '''
    def __init__(self):
        super().__init__('montecarlo')
        self.description = 'Create a monte carlo experiment.'


    def modifyParser(self, parser: ArgumentParser):
        parser.add_argument('--json', dest='json',
                            type=FileType('r'), required=True)
        super().modifyParser(parser)

    def run(self, args):
        id = UUID("00000000-0000-0000-0000-000000000000")
        storeFactory = CollectionStoreFactory()
        regionsStore = storeFactory.getStore('regions', RegionGroup.from_dict)
        config = json.load(args.json)
        group = config['group']
        regionGroups: list[RegionGroup] = [g for g in regionsStore.getItems() if g.group == group and (id == UUID(int=0) or g._id == id)]
        numAngles = config['numAngles']
        samples = config['numSamples']
        numPhi = config['numPhi']
        radius = config['radius']
        intersectionType = SampleStrategyIntersection(
            config['intersectionType'])
        cliqueRadius = config['cliqueRadius']
        solverType = SolverType(config['solverType'])
        k = 0
        faBounds = config['faBounds']
        gwfSlices = config['gwfSlices']
        hyperparameters = []
        dwellDistance = config['dwellDistance']
        leadDistance = config['leadDistance']
        multiplyDwell = config['multiplyDwell']


        headingStrategy = HeadingStrategyType(config['headingStrategy'])
        if headingStrategy == HeadingStrategyType.DWELL:
            edgeModification = EdgeModification(config.get('edgeModification', EdgeModification.DWELL))
        elif solverType == SolverType.LOW_ALTITUDE:
            edgeModification = EdgeModification.RAY_TRACED
        else:
            edgeModification = EdgeModification.NONE

        experimentStore = storeFactory.getStore(
            'experiments', Experiment.from_dict)


        for regionGroup in regionGroups:
            # dtsp 1d
            if SampleStrategyType.POINT in config['2dStrategies']:
                for angle in numAngles:
                    dtsp = makeExperiment(
                        solverType=solverType,
                        sampleType=SampleStrategyType.POINT,
                        edgeType=EdgeStrategyType.DUBINS_CAR,
                        numTheta=angle,
                        regions=regionGroup.regions,
                        radius=radius,
                        group=group,
                        regionType=RegionType.POINT,
                        headingStrategyType=HeadingStrategyType.UNIFORM
                    )
                    experimentStore.insertItem(dtsp)
                    k += 1
            # 2d tsps
            for angle in numAngles:
                for sample in samples:
                    # [SampleStrategyType.MAX_AREA_POLYGON, SampleStrategyType.MAX_AREA_EDGE]:
                    for sampleType in config['2dStrategies']:
                        if sampleType == SampleStrategyType.POINT:
                            continue
                        tsp2d = makeExperiment(
                            solverType=solverType,
                            sampleType=SampleStrategyType(sampleType),
                            edgeType=EdgeStrategyType.DUBINS_CAR,
                            numTheta=angle,
                            regions=regionGroup.regions,
                            radius=radius,
                            numSamples=sample,
                            regionType=RegionType.POLYGON,
                            group=group,
                            modification=edgeModification,
                            dwellDistance=dwellDistance,
                            leadDistance=leadDistance,
                            headingStrategyType=HeadingStrategyType.INWARD,
                            intersectionType=SampleStrategyIntersection.NON_INTERSECTING,
                            intersectionRadius=cliqueRadius
                        )
                        experimentStore.insertItem(tsp2d)
                        k += 1
            for sampleType in config['3dStrategies']:
                # additional parameters for sample stratgies
                hyperparameters = []
                if sampleType == SampleStrategyType.GLOBAL_WEIGHTED_FACE:
                    hyperparameters = [gwfSlices]

                for sample in samples:
                    for angle in numAngles:
                        for phi in numPhi:
                            phiRange = faBounds if phi > 1 else [0, 0]
                            dtsp3d = makeExperiment(
                                solverType=solverType,
                                sampleType=SampleStrategyType(sampleType),
                                numTheta=angle,
                                numPhi=phi,
                                phiRange=phiRange,
                                numSamples=sample,
                                regions=regionGroup.regions,
                                radius=radius,
                                faBounds=faBounds,
                                group=group,
                                hyperparameters=hyperparameters,
                                modification=edgeModification,
                                dwellDistance=dwellDistance,
                                leadDistance=leadDistance,
                                headingStrategyType=headingStrategy,
                                intersectionType=intersectionType,
                                intersectionRadius=cliqueRadius,
                                multiplyDwell=multiplyDwell
                            )
                            experimentStore.insertItem(dtsp3d)
                            k += 1
                    if headingStrategy == HeadingStrategyType.DWELL:
                        continue
                    etsp3d = makeExperiment(
                        solverType=solverType,
                        sampleType=sampleType,
                        numSamples=sample,
                        regions=regionGroup.regions,
                        radius=radius,
                        faBounds=faBounds,
                        etsp2Dtsp=Etsp2DtspType.ALTERNATING_BISECTOR,
                        group=group,
                        hyperparameters=hyperparameters,
                        modification=edgeModification,
                        dwellDistance=dwellDistance,
                        headingStrategyType=headingStrategy,
                        intersectionType=intersectionType,
                        intersectionRadius=cliqueRadius
                    )
                    experimentStore.insertItem(etsp3d)
                    k += 1
        experimentStore.close()
        regionsStore.close()
        return k
