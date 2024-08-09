from viewplanning.sampling.sampleStrategy import SampleStrategy
from viewplanning.sampling.sampleHelpers import iterateRegions, containsPoint3d
from .helpers import checkMultiRegion, Volume, MultiSampleStrategy
from viewplanning.models import VertexMulti, Region
from typing import Iterator
import pyvista as pv


SAMPLING_DISTANCE = 600


class SimpleIntersectingVolumeSampling(SampleStrategy):
    '''
    Samples are allocated and then the samples that happend to be in multiple visiblity are allocated to those volumes
    by chekcing if the (x,y,z) point in in the mesh.
    '''
    def __init__(self, method: MultiSampleStrategy):
        '''
        Parameters
        ----------
        method: MultiSampleStrategy
            method to sample the volumes with
        '''
        self.method = method

    def getSamples(self, regions: 'Iterator[Region]') -> 'list[VertexMulti]':

        regions: list[Region] = list(regions)
        meshes: list[pv.PolyData] = list(iterateRegions(regions))

        # intersect meshes for subregions
        volumes: list[Volume] = []
        for i, mesh in enumerate(meshes):
            volumes.append(
                Volume([i], mesh, self.method.numSamples, mesh.volume))

        # get samples from sample method
        samples = self.method.sampleMeshes(volumes, meshes, regions)
        return checkMultiRegion(samples, meshes, containsPoint3d)
