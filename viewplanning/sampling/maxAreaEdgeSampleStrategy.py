from viewplanning.sampling.sampleStrategy import SampleStrategy
from typing import Iterator
from viewplanning.models import Region, RegionType, Vertex2D
import pyvista as pv
import numpy as np
from viewplanning.sampling.sampleHelpers import SamplingFailedException, iterateRegions, polygonFromBody


SLICES = 64


class MaxAreaEdgeSampleStrategy(SampleStrategy):
    """
    Does obermeyer 2d sampling at global area maximum or minimum at highest view volume
    """

    def __init__(self, numSamples, numAngles):
        super().__init__()
        self.numSamples = numSamples
        self.numAngles = numAngles

    def getSamples(self, bodies: 'Iterator[Region]') -> 'list[Vertex2D]':
        points = []
        bodies: list[pv.PolyData] = list(iterateRegions(bodies, RegionType.WAVEFRONT))
        # find global min and max
        globalZMin = min([body.bounds[4] for body in bodies])
        globalZMax = max([body.bounds[5] for body in bodies])

        zSlices = np.linspace(globalZMin, globalZMax, SLICES)
        areas = np.zeros([len(bodies), SLICES])
        # slice all along global z slices
        polygons = []
        for j, body in enumerate(bodies):
            for i, z in enumerate(zSlices):
                polygon = polygonFromBody(z, body)
                polygons.append(polygon)
                if polygon is None:
                    continue
                areas[j, i] = polygon.area
        s = np.sum(areas, axis=0)
        i = np.array([list(range(SLICES))] * len(bodies))
        i[areas <= 0] = SLICES
        idx = np.max(np.min(i, axis=1))
        idx = max(np.argmax(s[idx:]), idx)
        zhat = zSlices[idx]

        for group, body in enumerate(bodies):
            polygon = polygonFromBody(zhat, body)
            if polygon is None:
                raise SamplingFailedException(f'Couldn\'t slice mesh into polygon at z level {zhat}')
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
                for k in range(self.numAngles):
                    points.append(Vertex2D(group=str(group), x=point[0], y=point[1], theta=startAngle + np.pi * k / (self.numAngles - 1)))
        return points
