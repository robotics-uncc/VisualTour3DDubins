from typing import Generator, Iterator
import numpy as np
from viewplanning.models import Region, Vertex3D
from viewplanning.sampling.sampleStrategy import SampleStrategy
from viewplanning.sampling.sampleHelpers import SamplingFailedException, polygonFromBody, iterateRegions, getPointsOnEdge
from shapely.geometry import Polygon
import pyvista as pv
import math

OFFSET_INTO_BODY = .005
POLYGON_CUTOFF = .1
LIMIT = 200


class GlobalPerimeterWeightedFaceSampleStrategy(SampleStrategy[Region]):
    '''
    Samples the surface of the volumes according to the global surface area distribution.
    Samples pitch angles uniformly between supplied values.
    '''
    def __init__(self, numSamples, numPhi, phiRange: 'list[float]', numLevels, headingStrategy):
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
        numLevels: int
            numbe of z plane slices to assign samples on
        '''
        super().__init__(headingStrategy)
        self.numSamples = numSamples
        self.numPhi = numPhi
        self.phiRange = phiRange
        self.numSlices = numLevels

    def getSamples(self, regions: 'Iterator[Region]') -> 'list[Vertex3D]':
        samples = []
        bodies: list[pv.PolyData] = list(iterateRegions(regions))

        if len(bodies) <= 0:
            return []

        # find global min and max
        globalZMin = min([body.bounds[4] for body in bodies])
        globalZMax = max([body.bounds[5] for body in bodies])
        # move slightly up and down
        r = globalZMax - globalZMin
        globalZMin += r * OFFSET_INTO_BODY
        globalZMax -= r * OFFSET_INTO_BODY
        # # find characteristic length of surface area
        # globalArea = sum(map(self._surfaceArea, bodies))
        # globalL = np.sqrt(globalArea / max(self.numSamples - 2, 1))
        # # number of z slices add two for top and bottom of view region
        # totalZ = int(np.floor((globalZMax - globalZMin) / globalL) + 2)
        totalZ = self.numSlices

        bodyInfo = []
        zLengths = [0] * totalZ
        # slice all bodies along global z slices
        for body in bodies:
            item = {
                'body': body,
                'slices': []
            }
            i = 0
            for z in np.linspace(globalZMin, globalZMax, totalZ):
                polygon = polygonFromBody(z, body, cutoff=POLYGON_CUTOFF)
                if polygon is None:
                    i += 1
                    item['slices'].append({'z': z, 'polygon': None})
                    continue
                item['slices'].append({'z': z, 'polygon': polygon})
                # total lengths along global z slices
                zLengths[i] += polygon.exterior.length
                i += 1
            bodyInfo.append(item)
        for group, bi in enumerate(bodyInfo):
            samplesPerBody = self._iterateNumSamplesPerBody(bi, zLengths)
            s = []
            for numPoints, polygon, z in samplesPerBody:
                if numPoints <= 0 or polygon is None:
                    continue
                s += self._sampleSlice(numPoints, polygon, z, group)
            if len(s) <= 0:
                raise SamplingFailedException(f'failed to sample view region {regions[group].file}')
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

    def _surfaceArea(self, body: pv.PolyData):
        areas = np.array([.5 * np.linalg.norm(np.cross(
            body.points[body.faces.reshape(-1, 4)[i, 1], :] - body.points[body.faces.reshape(-1, 4)[i, 2], :],
            body.points[body.faces.reshape(-1, 4)[i, 1], :] - body.points[body.faces.reshape(-1, 4)[i, 3], :]
        )) for i in range(body.n_cells)])
        return np.sum(areas)

    # included to make sure view regions that don't have the same min and max get their top and bottom polygons samples
    def _iterateNumSamplesPerBody(self, bodyInfo, zLengths) -> 'Generator[(int, Polygon, float), None, None]':
        j = 0
        _, _, _, _, bodyMin, bodyMax = bodyInfo['body'].bounds
        r = bodyMax - bodyMin
        bodyMin += r * OFFSET_INTO_BODY
        bodyMax -= r * OFFSET_INTO_BODY
        inBodySlices = []
        newZ = []
        while bodyMin > bodyInfo['slices'][j]['z']:
            j += 1
        if j > 0:
            inBodySlices.append({'z': bodyMin, 'polygon': polygonFromBody(bodyMin, bodyInfo['body'], cutoff=POLYGON_CUTOFF)})
            length = (zLengths[j] - zLengths[j - 1]) / (bodyInfo['slices'][j]['z'] - bodyInfo['slices'][j - 1]['z']) \
                * (bodyMin - bodyInfo['slices'][j - 1]['z']) + zLengths[j - 1]
            newZ.append(length)
        while j < len(bodyInfo['slices']) and bodyMax > bodyInfo['slices'][j]['z']:
            inBodySlices.append(bodyInfo['slices'][j])
            newZ.append(zLengths[j])
            j += 1

        if j < len(zLengths):
            length = (zLengths[j] - zLengths[j - 1]) / (bodyInfo['slices'][j]['z'] - bodyInfo['slices'][j - 1]['z']) \
                * (bodyMax - bodyInfo['slices'][j - 1]['z']) + zLengths[j - 1]
            newZ.append(length)
            inBodySlices.append({'z': bodyMax, 'polygon': polygonFromBody(bodyMax, bodyInfo['body'], cutoff=POLYGON_CUTOFF)})

        totalZ = sum(newZ)
        allocations = newZ / totalZ * self.numSamples
        allocationsInt = np.floor(allocations).astype(np.int32)
        fracs = allocations - allocationsInt
        order = np.flip(np.argsort(fracs))
        allocated = np.sum(allocationsInt)
        for i in range(self.numSamples - allocated):
            allocationsInt[order[i % len(order)]] += 1
        return [(allocationsInt[i], inBodySlices[i]['polygon'], inBodySlices[i]['z']) for i in range(len(newZ))]
