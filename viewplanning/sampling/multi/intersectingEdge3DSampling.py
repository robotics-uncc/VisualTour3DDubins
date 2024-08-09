from .helpers import MultiSampleStrategy, Volume
from viewplanning.sampling import polygonFromBody, getPointsOnEdge, SamplingFailedException
from viewplanning.models import Region, VertexMulti, Vertex3DMulti
import pyvista as pv
import numpy as np

OFFSET = .01
INTERSECTION_CUTOFF = 1e-3
LIMIT = 200 


class IntersectingEdge3DSampling(MultiSampleStrategy):
    '''
    Samples to bottom edge of the visibility volumes. Samples inward pointing heading angles.
    Samples pitch angles uniformly between supplied values.
    Considers the intersection of visiblity volumes.
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
        super().__init__(numSamples, headingStrategy)
        self.numPhi = numPhi
        self.phiRange = phiRange

    def sampleMeshes(self, volumes: 'list[Volume]', meshes: 'list[pv.PolyData]', regions: 'list[Region]') -> 'list[VertexMulti]':
        samples = []
        for volume in volumes:
            _, _, _, _, zMin, zMax = volume.volume.bounds
            z = (zMax - zMin) * OFFSET + zMin
            polygon = polygonFromBody(z, volume.volume, cutoff=INTERSECTION_CUTOFF)
            if polygon is None:
                raise SamplingFailedException(f'failed to sample {volume.parents}')
            s = self._sampleSlice(volume.samples, polygon, z, volume.parents[0], volume.parents)
            samples += s
        return samples

    def _sampleSlice(self, numPoints, polygon, z, group, visits):
        samples = []
        pointsIndex = 0
        remainingSamples = numPoints * self.headingStrategy.numHeadings * self.numPhi
        lr = remainingSamples
        i = 0
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
                        samples.append(Vertex3DMulti(
                            group=group,
                            visits=set(map(str, visits)),
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
