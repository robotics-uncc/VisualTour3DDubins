from viewplanning.sampling.sampleStrategy import SampleStrategy
from viewplanning.models import Region, RegionType, Vertex2D
import pyvista as pv
import numpy as np
from viewplanning.sampling.sampleHelpers import SamplingFailedException, iterateRegions, polygonFromBody, getPointsOnEdge
import logging


SLICES = 64
Z_SLICE_TOLERANCE = .01
LIMIT = 200


class MaxAreaEdgeSampleStrategy(SampleStrategy):
    """
    Does obermeyer 2d sampling at global area maximum or minimum at highest view volume
    """

    def __init__(self, numSamples, headingStrategy):
        '''
        Parameters
        ----------
        numSamples: int
            number of (x, y, z) samples per volume
        headingStrategy: HeadingStrategy
            how to allocate headings to the samples theta
        '''
        super().__init__(headingStrategy)
        self.numSamples = numSamples

    def getSamples(self, regions: 'list[Region]') -> 'list[Vertex2D]':
        samples = []
        bodies: list[pv.PolyData] = list(iterateRegions(regions, RegionType.WAVEFRONT))
        # find global min and max
        globalZMin = min([body.bounds[4] for body in bodies])
        globalZMax = max([body.bounds[5] for body in bodies])

        zSlices = np.linspace(globalZMin, globalZMax, SLICES)
        areas = np.zeros([len(bodies), SLICES])
        # slice all along global z slices
        polygons = []
        for j, body in enumerate(bodies):
            for i, z in enumerate(zSlices):
                if z < body.bounds[4] or z > body.bounds[5]:
                    continue
                polygon = polygonFromBody(z, body, cutoff=Z_SLICE_TOLERANCE)
                polygons.append(polygon)
                if polygon is None:
                    logging.warning(f"failed to slice mesh {regions[j].file} into polygon a z level {z}")
                    continue
                areas[j, i] = polygon.area
        s = np.sum(areas, axis=0)
        i = np.array([list(range(SLICES))] * len(bodies))
        i[areas <= 0] = SLICES
        idx = np.max(np.min(i, axis=1))
        idx = max(np.argmax(s[idx:]), idx)
        zhat = zSlices[idx]
        if (areas[:, idx] <= 0).any():
            raise SamplingFailedException(f'Couldn\'t find level that slices all meshes {regions[0].file}')

        for group, body in enumerate(bodies):
            polygon = polygonFromBody(zhat, body, cutoff=Z_SLICE_TOLERANCE)
            if polygon is None:
                zI = int(np.argmax(list(map(lambda x: x.z, regions))))
                raise SamplingFailedException(
                    f'Couldn\'t slice mesh {regions[group].file} into polygon at z level {zhat} highest min height {regions[zI].z} on region {regions[zI].file}')
            s = self._sampleSlice(self.numSamples, polygon, z, group)
            samples += s
        return samples

    def _sampleSlice(self, numPoints, polygon, z, group):
        samples = []
        pointsIndex = 0
        remainingSamples = numPoints * self.headingStrategy.numHeadings
        i = 0
        lr = remainingSamples
        while remainingSamples > 0 and i < LIMIT:
            points = getPointsOnEdge(pointsIndex, int(np.ceil(remainingSamples / (self.headingStrategy.numHeadings))), polygon)
            pointsIndex += numPoints
            for point in points:
                for theta in self.headingStrategy.getHeadings(np.array([point[0], point[1], z]), polygon=polygon):
                    if remainingSamples <= 0:
                        return samples
                    samples.append(Vertex2D(
                        group=str(group),
                        x=point[0],
                        y=point[1],
                        theta=theta
                    ))
                    remainingSamples -= 1
            if lr == remainingSamples:
                i += 1
            lr = remainingSamples
        return samples
