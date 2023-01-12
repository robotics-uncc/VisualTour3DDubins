import numpy as np
from viewplanning.models import SolverType, RegionType, RegionGroup, SampleStrategyType, Experiment, Etsp2DtspType, makeExperiment
from viewplanning.store import MongoCollectionStore
from viewplanning.cli.subapplication import Subapplication
from argparse import ArgumentParser


class MonteCarloExperiments(Subapplication):
    def __init__(self):
        super().__init__('montecarlo')
        self.description = 'Create a monte carlo experiment.'

    def modifyParser(self, parser: ArgumentParser):
        parser.add_argument('group', type=str, help='target group name to make experiment for')
        super().modifyParser(parser)

    def run(self, args):
        regionsStore = MongoCollectionStore[RegionGroup]('regions', RegionGroup.from_dict)
        regionGroups: list[RegionGroup] = [group for group in regionsStore.getItems() if group.group == args.group]
        numAngles = [2, 4, 8]
        samples = [2, 4, 8, 16, 32]
        numPhi = [1, 3]
        radius = 40
        k = 0
        faBounds = [-np.pi / 12, np.pi / 9]
        neighborAlpha = [.1, .5, .9]
        neighborBeta = [1, 10, 100]
        neighborN = [2, 4, 5]
        experimentStore = MongoCollectionStore[Experiment]('experiments', Experiment.from_dict)
        for regionGroup in regionGroups:
            # dtsp 1d
            for angle in numAngles:
                dtsp = makeExperiment(solverType=SolverType.TWO_D, sampleType=SampleStrategyType.POINT, numTheta=angle, regions=regionGroup.regions, radius=radius, group=args.group, regionType=RegionType.POINT)
                experimentStore.insertItem(dtsp)
                k += 1
            # 2d tsps
            for angle in numAngles:
                for sample in samples:
                    for sampleType in [SampleStrategyType.MAX_AREA_POLYGON, SampleStrategyType.MAX_AREA_EDGE]:
                        tsp2d = makeExperiment(solverType=SolverType.TWO_D, sampleType=sampleType, numTheta=angle, regions=regionGroup.regions, radius=radius, numSamples=sample, regionType=RegionType.POLYGON, group=args.group)
                        experimentStore.insertItem(tsp2d)
                        k += 1
            # 3d tsps
            for sampleType in [SampleStrategyType.EDGE_3D, SampleStrategyType.BODY, SampleStrategyType.FACE, SampleStrategyType.GLOBAL_WEIGHTED_FACE]:
                for sample in samples:
                    etsp3d = makeExperiment(solverType=SolverType.THREE_D_MODIFIED_DISTANCE, sampleType=sampleType, numSamples=sample, regions=regionGroup.regions, radius=radius, faBounds=faBounds, etsp2Dtsp=Etsp2DtspType.ALTERNATING_BISECTOR, group=args.group)
                    experimentStore.insertItem(etsp3d)
                    k += 1
                    for angle in numAngles:
                        for phi in numPhi:
                            phiRange = faBounds if phi > 1 else [0, 0]
                            dtsp3d = makeExperiment(solverType=SolverType.THREE_D, sampleType=sampleType, numTheta=angle, numPhi=phi, phiRange=phiRange, numSamples=sample, regions=regionGroup.regions, radius=radius, faBounds=faBounds, group=args.group)
                            experimentStore.insertItem(dtsp3d)
                        k += 1

        return k
