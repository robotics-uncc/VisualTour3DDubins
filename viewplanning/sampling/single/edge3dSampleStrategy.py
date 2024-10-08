import numpy as np
from viewplanning.models import Region, Vertex3D, RegionType
from viewplanning.sampling.sampleStrategy import SampleStrategy
from viewplanning.sampling.sampleHelpers import iterateRegions, polygonFromBody, getPointsOnEdge, SamplingFailedException
from typing import Iterator

OFFSET = .01
POLYGON_CUTOFF = .01
LIMIT = 200


class Edge3dSampleStrategy(SampleStrategy[Region]):
    '''
    Samples to bottom edge of the visibility volumes.
    Samples pitch angles uniformly between supplied values.
    '''
    def __init__(self, numSamples, numPhi, phiRange, headingStrategy):
        '''
        Parameters
        ----------
        numSamples: int
            number of (x, y, z) samples per volume
        headingStrategy: HeadingStrategy
            how to allocate headings to the samples theta
        numPhi: int
            number of pitch anlges per (X, y, z, theta) sample
        phiRange: list[float]
            acceptable range of pitch angles
        '''
        super().__init__(headingStrategy)
        self.numSamples = numSamples
        self.numPhi = numPhi
        self.phiRange = phiRange

    def getSamples(self, polygons: Iterator[Region]) -> 'list[Vertex3D]':
        samples = []
        regions = list(polygons)

        for group, mesh in enumerate(iterateRegions(regions, RegionType.WAVEFRONT)):
            _, _, _, _, zMin, zMax = mesh.bounds
            z = (zMax - zMin) * OFFSET + zMin
            polygon = polygonFromBody(z, mesh, cutoff=POLYGON_CUTOFF)
            if not polygon:
                raise SamplingFailedException(f'failed to slice mesh {group}')
            s = self._sampleSlice(self.numSamples, polygon, z, group)
            samples += s
        return samples

    def _sampleSlice(self, numPoints, polygon, z, group):
        samples = []
        pointsIndex = 0
        remainingSamples = numPoints * self.headingStrategy.numHeadings * self.numPhi
        i = 0
        lr = remainingSamples
        while remainingSamples > 0 and i < LIMIT:
            points = getPointsOnEdge(pointsIndex, int(np.ceil(remainingSamples / (self.headingStrategy.numHeadings * self.numPhi))), polygon)
            pointsIndex += numPoints
            for point in points:
                phiMag = self.phiRange[1] - self.phiRange[0]
                for theta in self.headingStrategy.getHeadings(np.array([point[0], point[1], z]), polygon=polygon):
                    for n in range(self.numPhi):
                        if remainingSamples <= 0:
                            return samples
                        phi = self.phiRange[0] + phiMag * n / (self.numPhi)
                        samples.append(Vertex3D(
                            group=str(group),
                            x=point[0],
                            y=point[1],
                            z=z,
                            theta=theta,
                            phi=phi
                        ))
                        remainingSamples -= 1
            if lr == remainingSamples:
                i += 1
            lr = remainingSamples
        return samples
