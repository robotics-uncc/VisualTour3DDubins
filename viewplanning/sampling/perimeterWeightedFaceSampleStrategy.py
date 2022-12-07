from typing import Iterator
import numpy as np
from viewplanning.sampling.sampleStrategy import SampleStrategy
from viewplanning.sampling.sampleHelpers import polygonFromBody, iterateRegions
from viewplanning.models import Region, Vertex3D
import pyvista as pv

OFFSET_INTO_BODY = .005


class PerimeterWeightedFaceSampleStrategy(SampleStrategy[Region]):
    def __init__(self, numSamples, numTheta, numPhi, phiRange: 'list[float]', nSlices: int):
        self.numSamples = numSamples
        self.numTheta = numTheta
        self.numPhi = numPhi
        self.phiRange = phiRange
        self.nSlices = nSlices

    def getSamples(self, bodies: 'Iterator[Region]') -> 'list[Vertex3D]':
        samples = []
        for group, body in enumerate(iterateRegions(bodies)):
            body: pv.PolyData
            _, _, _, _, zMin, zMax = body.bounds
            # move max and min slightly into view volume to get more consistent slice
            r = zMax - zMin
            zMin += r * OFFSET_INTO_BODY
            zMax -= r * OFFSET_INTO_BODY
            totalZ = np.floor((zMax - zMin) / self.nSlices)
            polygons = []
            for z in np.linspace(zMin, zMax, int(totalZ)):
                polygon = polygonFromBody(z, body)
                if polygon is None:
                    continue
                polygons.append((z, polygon))
            ppul = sum(map(lambda x: x[1].exterior.length, polygons)) / self.numSamples
            for z, polygon in polygons:
                perimeter = polygon.exterior.length
                segments = np.array(polygon.exterior.coords)
                j = 0
                travelDistance = 0
                a = segments[j + 1] - segments[j]
                d = np.linalg.norm(a)
                for i in range(int(np.floor(perimeter / ppul))):
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
                    phiMag = self.phiRange[1] - self.phiRange[0]
                    for k in range(self.numTheta):
                        for n in range(self.numPhi):
                            samples.append(Vertex3D(
                                group=str(group),
                                x=point[0],
                                y=point[1],
                                z=z,
                                theta=startAngle + np.pi * k / (self.numTheta - 1 if self.numTheta > 1 else 1),
                                phi=self.phiRange[0] + phiMag * n / (self.numPhi)
                            ))
        return samples
