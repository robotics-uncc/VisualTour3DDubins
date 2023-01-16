from typing import Generator, Iterator
import numpy as np
from viewplanning.models import Region, Vertex3D
from viewplanning.sampling.sampleStrategy import SampleStrategy
from viewplanning.sampling.sampleHelpers import SamplingFailedException, polygonFromBody, iterateRegions
from shapely.geometry import Polygon
import pyvista as pv

OFFSET_INTO_BODY = .005


class GlobalPerimeterWeightedFaceSampleStrategy(SampleStrategy[Region]):
    '''
    Samples the surface of the volumes according to the global surface area distribution.
    Samples inward pointing heading angles.
    Samples pitch angles uniformly between supplied values.
    '''

    def __init__(self, numSamples, numTheta, numPhi, phiRange: 'list[float]', numLevels: int):
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
        numLevels: int
            numbe of z plane slices to assign samples on
        '''
        self.numSamples = numSamples
        self.numTheta = numTheta
        self.numPhi = numPhi
        self.phiRange = phiRange
        self.numLevels = numLevels

    def getSamples(self, bodies: 'Iterator[Region]') -> 'list[Vertex3D]':
        samples = []
        bodies: list[pv.PolyData] = list(iterateRegions(bodies))

        if len(bodies) <= 0:
            return []

        # find global min and max
        globalZMin = min([body.bounds[4] for body in bodies])
        globalZMax = max([body.bounds[5] for body in bodies])

        bodyInfo = []
        zLengths = [0] * self.numLevels
        # slice all bodies along global z slices
        for body in bodies:
            item = {
                'body': body,
                'slices': []
            }
            i = 0
            for z in np.linspace(globalZMin, globalZMax, self.numLevels):
                polygon = polygonFromBody(z, body)
                if polygon is None:
                    i += 1
                    item['slices'].append(None)
                    continue
                item['slices'].append({'z': z, 'polygon': polygon})
                # total lengths along global z slices
                zLengths[i] += polygon.exterior.length
                i += 1
            bodyInfo.append(item)
        for group, bi in enumerate(bodyInfo):
            for numPoints, polygon, z in self._iterateNumSamplesPerBody(bi, zLengths, (globalZMax - globalZMin) / (self.numLevels - 1), globalZMin):
                if numPoints <= 0 or polygon is None:
                    continue
                perimeter = polygon.exterior.length
                ppul = perimeter / numPoints
                segments = np.array(polygon.exterior.coords)
                j = 0
                travelDistance = 0
                a = segments[j + 1] - segments[j]
                d = np.linalg.norm(a)
                for v in range(numPoints):
                    # advance to line where next point is in the middle of
                    while travelDistance < v * ppul:
                        a = segments[j + 1] - segments[j]
                        d = np.linalg.norm(a)
                        travelDistance += d
                        j += 1
                    t = travelDistance - ppul * v
                    point = segments[j] - t * a / np.linalg.norm(a)
                    # 0 to pi is external
                    startAngle = np.arctan2(a[1], a[0])
                    phiMag = self.phiRange[1] - self.phiRange[0]
                    for k in range(self.numTheta):
                        for n in range(self.numPhi):
                            theta = startAngle + np.pi * k / (self.numTheta - 1 if self.numTheta > 1 else 1)
                            phi = self.phiRange[0] + phiMag * n / (self.numPhi)
                            samples.append(Vertex3D(group=str(group), x=point[0], y=point[1], z=z, theta=theta, phi=phi))
        return samples

    def _surfaceArea(self, body: pv.PolyData):
        areas = np.array([.5 * np.linalg.norm(np.cross(body.cell_points(i)[:, 0] - body.cell_points(i)[:, 1], body.cell_points(i)[:, 0] - body.cell_points(i)[:, 2])) for i in range(body.n_cells)])
        return np.sum(areas)

    # included to make sure view regions that don't have the same min and max get their top and bottom polygons samples
    def _iterateNumSamplesPerBody(self, bodyInfo, zLengths, zStep, zMin) -> 'Generator[(int, Polygon, float), None, None]':
        _, _, _, _, bodyMin, bodyMax = bodyInfo['body'].bounds
        r = bodyMax - bodyMin
        bodyMin += r * OFFSET_INTO_BODY
        bodyMax -= r * OFFSET_INTO_BODY
        valid = []
        perimeters = []
        for j in range(len(bodyInfo['slices'])):
            slice = bodyInfo['slices'][j]
            z = zMin + zStep * j
            zl = zMin + zStep * (j - 1)
            zn = zMin + zStep * (j + 1)
            if slice is None and z < bodyMin and zn > bodyMin:
                slice = {'z': bodyMin, 'polygon': polygonFromBody(bodyMin, bodyInfo['body'])}
                perimeters.append(self._interpolate(j, bodyMin, z, zl, zn, zLengths))
            elif slice is None and zl < bodyMax and z > bodyMax:
                slice = {'z': bodyMax, 'polygon': polygonFromBody(bodyMax, bodyInfo['body'])}
                perimeters.append(self._interpolate(j, bodyMax, z, zl, zn, zLengths))
            elif slice is None:
                continue
            else:
                perimeters.append(zLengths[j])
            valid.append(slice)
        perimeters = np.array(perimeters)
        n = np.floor(perimeters / np.sum(perimeters) * self.numSamples)
        dn = (perimeters / np.sum(perimeters) * self.numSamples) - n
        for _ in range(int(self.numSamples - np.sum(n))):
            q = np.argmax(dn)
            n[q] += 1
            dn[q] = 0
        for j in range(len(valid)):
            yield int(n[j]), valid[j]['polygon'], valid[j]['z']

    def _interpolate(self, j, t, x, xl, xn, yArr):
        if j + 1 < len(yArr):
            return (yArr[j + 1] - yArr[j]) / (xn - x) * (t - x) + yArr[j]
        elif j - 1 > 0:
            return (yArr[j] - yArr[j - 1]) / (x - xl) * (t - xl) + yArr[j - 1]
