from viewplanning.sampling.sampleStrategy import SampleStrategy
from typing import Iterator
from viewplanning.models import Region, RegionType, Vertex2D
import pyvista as pv
import numpy as np
from viewplanning.sampling.sampleHelpers import SamplingFailedException, iterateRegions, polygonFromBody, containsPoint2d


SLICES = 64


class MaxAreaPolygonSampleStrategy(SampleStrategy):
    """
    Does obermeyer 2d sampling at maximum area slice that goes through all view volumes
    """

    def __init__(self, numSamples, numAngles):
        super().__init__()
        self.matrixEdge = int(np.floor(np.sqrt(numSamples)))
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
        idx = idx + np.argmax(s[idx:])
        zhat = zSlices[idx]

        for group, body in enumerate(bodies):
            polygon = polygonFromBody(zhat, body)
            if polygon is None:
                raise SamplingFailedException('Couldn\'t slice mesh into polygon')
            xMin, yMin, xMax, yMax = polygon.bounds
            for x in np.linspace(xMin, xMax, self.matrixEdge):
                for y in np.linspace(yMin, yMax, self.matrixEdge):
                    if not containsPoint2d([x, y], polygon):
                        continue
                    for theta in np.linspace(0, 2 * np.pi * (self.numAngles - 1) / self.numAngles, self.numAngles):
                        points.append(Vertex2D(group=str(group), x=x, y=y, theta=theta))
        return points
