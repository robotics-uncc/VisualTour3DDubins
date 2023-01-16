import numpy as np
from viewplanning.models import Region, Vertex3D, RegionType
from viewplanning.sampling.sampleStrategy import SampleStrategy
from viewplanning.sampling.sampleHelpers import iterateRegions, SamplingFailedException, polygonFromBody
from typing import Iterator

OFFSET = .01


class Edge3dSampleStrategy(SampleStrategy[Region]):
    '''
    Samples to bottom edge of the visibility volumes. Samples inward pointing heading angles.
    Samples pitch angles uniformly between supplied values.
    '''

    def __init__(self, numSamples, numTheta, numPhi, phiRange):
        '''
        Parameters
        ----------
        numSamples: int
            number of (x, y, z) samples per volume
        numTheta: int
            number of heading angles per (x, y, z) sample
        numPhi: int
            number of pitch anlges per (X, y, z, theta) sample
        phiRange: list[float]
            acceptable range of pitch angles
        '''
        super().__init__()
        self.numSamples = numSamples
        self.numTheta = numTheta
        self.numPhi = numPhi
        self.phiRange = phiRange

    def getSamples(self, polygons: Iterator[Region]) -> 'list[Vertex3D]':
        points = []
        regions = list(polygons)

        for group, mesh in enumerate(iterateRegions(regions, RegionType.WAVEFRONT)):
            _, _, _, _, zMin, zMax = mesh.bounds
            z = (zMax - zMin) * OFFSET + zMin
            polygon = polygonFromBody(z, mesh)
            if not polygon:
                continue
            perimeter = polygon.exterior.length
            segments = np.array(polygon.exterior.coords)
            ppul = perimeter / self.numSamples
            j = 0
            travelDistance = 0
            a = segments[j + 1] - segments[j]
            d = np.linalg.norm(a)
            for i in range(self.numSamples):
                # advance to line where next point is in the middle of
                while travelDistance < i * ppul:
                    a = segments[j + 1] - segments[j]
                    d = np.linalg.norm(a)
                    travelDistance += d
                    j += 1
                t = travelDistance - ppul * i
                point = segments[j] - t * a / np.linalg.norm(a)
                # 0 to pi is external
                startAngle = np.arctan2(a[1], a[0])
                for k in range(self.numTheta):
                    for m in range(self.numPhi):
                        points.append(Vertex3D(
                            group=str(group),
                            x=point[0],
                            y=point[1],
                            z=z,
                            theta=startAngle + np.pi * k / (self.numTheta - 1 if self.numTheta > 1 else 1),
                            phi=self.phiRange[0] + (self.phiRange[1] - self.phiRange[0]) * m / (self.numPhi)
                        ))
        return points
