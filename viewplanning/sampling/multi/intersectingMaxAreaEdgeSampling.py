from .helpers import MultiSampleStrategy, Volume
from viewplanning.sampling.sampleHelpers import polygonFromBody, SamplingFailedException, getPointsOnEdge
from viewplanning.models import Region, VertexMulti, Vertex2DMulti
from viewplanning.sampling.heading import HeadingStrategy
import pyvista as pv
import numpy as np

OFFSET = .01
SLICES = 64


class IntersectingMaxAreaEdgeSampling(MultiSampleStrategy):
    """
    Does obermeyer 2d sampling at global area maximum or minimum at highest view volume.
    Considers the intersecion of visibility volumes
    """

    def __init__(self, numSamples, headingStrategy: HeadingStrategy):
        '''
        Parameters
        ----------
        numSamples: int
            number of (x, y, z) samples per volume
        headingStrategy: HeadingStrategy
            how to allocate headings to the samples theta
        '''
        super().__init__(numSamples, headingStrategy)

    def sampleMeshes(self, volumes: 'list[Volume]', meshes: 'list[pv.PolyData]', regions: 'list[Region]') -> 'list[VertexMulti]':
        samples: 'list[Vertex2DMulti]' = []
        globalZMin = min([volume.volume.bounds[4] for volume in volumes])
        globalZMax = max([volume.volume.bounds[5] for volume in volumes])

        zSlices = np.linspace(globalZMin, globalZMax, SLICES)
        areas = np.zeros([len(volumes), SLICES])
        # slice all along global z slices
        polygons = []
        for j, volume in enumerate(volumes):
            for i, z in enumerate(zSlices):
                polygon = polygonFromBody(z, volume.volume)
                polygons.append(polygon)
                if polygon is None:
                    continue
                areas[j, i] = polygon.area
        s = np.sum(areas, axis=0)
        i = np.array([list(range(SLICES))] * len(volumes))
        i[areas <= 0] = SLICES
        idx = np.max(np.min(i, axis=1))
        idx = max(np.argmax(s[idx:]), idx)
        zhat = zSlices[idx]

        for volume in volumes:
            polygon = polygonFromBody(zhat, volume.volume)
            if polygon is None:
                raise SamplingFailedException(
                    f'Couldn\'t slice mesh into polygon at z level {zhat}')
            s = self._sampleSlice(self.numSamples, polygon,
                                  volume.parents[0], volume.parents)
            samples += s

        return samples

    def _sampleSlice(self, numPoints, polygon, group, visits):
        samples = []
        pointsIndex = 0
        remainingSamples = numPoints * self.headingStrategy.numHeadings
        while remainingSamples > 0:
            points = getPointsOnEdge(pointsIndex, int(
                np.ceil(remainingSamples / (self.headingStrategy.numHeadings))), polygon)
            pointsIndex += numPoints
            for point in points:
                for theta in self.headingStrategy.getHeadings(np.array([point[0], point[1], z]), polygon=polygon):
                    if remainingSamples <= 0:
                        return samples
                    samples.append(Vertex2DMulti(
                        group=group,
                        visits=set(map(str, visits)),
                        x=point[0],
                        y=point[1],
                        theta=theta
                    ))
                    remainingSamples -= 1
        return samples
