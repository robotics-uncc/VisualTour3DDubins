from viewplanning.sampling.sampleStrategy import SampleStrategy
from viewplanning.sampling.sampleHelpers import iterateRegions, SamplingFailedException
from .helpers import findCliques, MultiSampleStrategy, makeDuplicateNodes, IntersectionStore, Volume
from viewplanning.models import VertexMulti, Region
from typing import Iterator
import pyvista as pv
from math import sqrt
import logging
import os


APPROX_ZERO = 1e-3


class BruteVolumeSampling(SampleStrategy):
    '''
    Sample visiblity volumes and the intersection of visbility volumes are found using a clique graph
    with the same number of samples for visiblity volumes and the intersection of visiblity volumes.
    '''
    def __init__(self, method: MultiSampleStrategy, cliqueRadius: float, cliqueLimit: int):
        '''
        Parameters
        ----------
        method: MultiSampleStrategy
            method to sample the volumes with
        cliqueRadius: float
            distance between visbiltiy volumes to consider intersecting
        cliqueLimit: int
            consider cliques up to and including this clique number
        '''
        super().__init__(None)
        self.method = method
        self.cliqueRadius = cliqueRadius
        self.cliqueLimit = cliqueLimit
        self.method = method
        self.headingStrategy = method.headingStrategy

    def getSamples(self, regions: 'Iterator[Region]') -> 'list[VertexMulti]':
        try:
            regions: list[Region] = list(regions)
            meshes: list[pv.PolyData] = list(iterateRegions(regions))

            # intersect meshes for subregions
            volumes: list[Volume] = []
            for i, mesh in enumerate(meshes):
                volumes.append(
                    Volume([str(i)], mesh, self.method.numSamples, mesh.volume))
            logging.debug(f'finding cliques for pid {os.getpid()}')
            cliques = findCliques(
                regions,
                self.cliqueRadius,
                clique_limit=self.cliqueLimit,
                dwell=self.headingStrategy.dwellDistance,
                multDwell=self.headingStrategy.multiplyDwell
            )
            logging.debug(f'intersecting meshes for pid {os.getpid()} # of cliques {len(cliques)}')
            for group in cliques:
                if len(group) <= 1:
                    continue
                mesh = intersectMeshes(group, meshes, regions)
                if not mesh or mesh.n_cells <= 0:
                    continue
                x_min, x_max, y_min, y_max, _, _ = mesh.bounds
                k = sqrt((x_max - x_min) ** 2 + (y_max - y_min) ** 2)
                if self.headingStrategy.multiplyDwell:
                    d = self.headingStrategy.dwellDistance * len(group)
                else:
                    d = self.headingStrategy.dwellDistance
                if k < d:
                    continue
                volumes.append(Volume(list(map(str, group)), mesh, self.method.numSamples, mesh.volume))

            logging.debug(f'finding samples points for pid {os.getpid()}')
            # get samples from sample method
            samples = self.method.sampleMeshes(volumes, meshes, regions)
            # return checkMultiRegion(samples, meshes, containsPoint3d)
            # if len(set([s.group for s in samples])) != len(meshes):
            #     raise SamplingFailedException('Failed to Sample all Meshes')
            return makeDuplicateNodes(samples)
        finally:
            store = IntersectionStore.getInstance()
            store.clearCache()


def intersectMeshes(indices, meshes: 'list[pv.PolyData]', regions: 'list[Region]') -> pv.PolyData:
    result = meshes[indices[0]]
    store = IntersectionStore.getInstance()
    for k, i in enumerate(indices[1:], 1):
        result = store.intersect(
            result,
            meshes[i],
            '-'.join([os.path.basename(regions[j].file) for j in indices[:k]]),
            os.path.basename(regions[i].file)
        )
    return result
