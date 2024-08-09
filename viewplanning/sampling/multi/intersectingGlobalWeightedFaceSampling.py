from .helpers import MultiSampleStrategy, Volume
from typing import Generator
import numpy as np
from viewplanning.models import Region, Vertex3DMulti
from viewplanning.sampling.sampleHelpers import SamplingFailedException, polygonFromBody, getPointsOnEdge
from shapely.geometry import Polygon
import pyvista as pv


OFFSET_INTO_BODY = .005
POLYGON_CUTOFF = .1
LIMIT = 200


class IntersectingGlobalWeightedFaceSampling(MultiSampleStrategy):
    '''
    Samples the surface of the volumes according to the global surface area distribution.
    Samples pitch angles uniformly between supplied values.
    Considers the intersecion of visiblity volumes
    '''
    def __init__(self, numSamples, numPhi, phiRange: 'list[float]', numLevels: int, headingStrategy):
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
        super().__init__(numSamples, headingStrategy)
        self.numPhi = numPhi
        self.phiRange = phiRange
        self.numLevels = numLevels

    def sampleMeshes(self, volumes: 'list[Volume]', meshes: 'list[pv.PolyData]', regions: 'list[Region]') -> 'list[Vertex3DMulti]':
        samples: 'list[Vertex3DMulti]' = []
        globalZMin = min([volume.volume.bounds[4] for volume in volumes])
        globalZMax = max([volume.volume.bounds[5] for volume in volumes])
        r = globalZMax - globalZMin
        globalZMin += r * OFFSET_INTO_BODY
        globalZMax -= r * OFFSET_INTO_BODY

        bodyInfo = []
        zLengths = [0] * self.numLevels
        # slice all bodies along global z slices
        for volume in volumes:
            item = {
                'body': volume,
                'slices': []
            }
            i = 0
            for z in np.linspace(globalZMin, globalZMax, self.numLevels):
                polygon = polygonFromBody(z, volume.volume, cutoff=POLYGON_CUTOFF)
                if polygon is None:
                    i += 1
                    item['slices'].append({'z': z, 'polygon': None})
                    continue
                item['slices'].append({'z': z, 'polygon': polygon})
                # total lengths along global z slices
                zLengths[i] += polygon.exterior.length
                i += 1
            bodyInfo.append(item)
        for bi in bodyInfo:
            s = []
            for numPoints, polygon, z in self._iterateNumSamplesPerBody(bi, zLengths):
                if numPoints <= 0 or polygon is None:
                    continue
                samp = self._sampleSlice(
                    numPoints,
                    polygon,
                    z,
                    bi['body'].parents[0],
                    bi['body'].parents
                )
                s += samp
            samples += s
        return samples

    def _surfaceArea(self, body: pv.PolyData):
        areas = np.array([.5 * np.linalg.norm(np.cross(
            body.points[body.faces.reshape(-1, 4)[i, 1], :] - body.points[body.faces.reshape(-1, 4)[i, 2], :],
            body.points[body.faces.reshape(-1, 4)[i, 1], :] - body.points[body.faces.reshape(-1, 4)[i, 3], :]
        )) for i in range(body.n_faces)])
        return np.sum(areas)
        totalArea = sum(zLengths)
        while i < len(bodyInfo['slices']) - 1 \
                and (bodyInfo['slices'][i] is None or bodyInfo['slices'][i]['z'] < bodyMin):
            bottomArea += zLengths[i]
            i += 1
        if bottomArea > 0:
            yield int(np.floor(self.numSamples * bottomArea / totalArea)), \
                polygonFromBody(bodyMin, bodyInfo['body'].volume), \
                bodyMin
        while i < len(bodyInfo['slices']) and (bodyInfo['slices'][i] is None or bodyInfo['slices'][i]['z'] < bodyMax):
            if bodyInfo['slices'][i] is None:
                allNone = True
                for slice in bodyInfo['slices'][i:]:
                    allNone = allNone and slice is None
                if allNone:
                    break
                i += 1
                continue
            yield int(np.floor(self.numSamples * zLengths[i] / totalArea)), \
                bodyInfo['slices'][i]['polygon'], \
                bodyInfo['slices'][i]['z']
            i += 1
        topArea = 0
        while i < len(zLengths):
            topArea += zLengths[i]
            i += 1
        if topArea > 0:
            yield int(np.floor(self.numSamples * topArea / totalArea)), \
                polygonFromBody(bodyMax, bodyInfo['body'].volume), \
                bodyMax

    # included to make sure view regions that don't have the same min and max get their top and bottom polygons samples
    def _iterateNumSamplesPerBody(self, bodyInfo, zLengths) -> 'Generator[(int, Polygon, float), None, None]':
        i = 0
        _, _, _, _, bodyMin, bodyMax = bodyInfo['body'].volume.bounds
        r = bodyMax - bodyMin
        bodyMin += r * OFFSET_INTO_BODY
        bodyMax -= r * OFFSET_INTO_BODY
        inBodySlices = []
        newZ = []
        while bodyMin > bodyInfo['slices'][i]['z']:
            i += 1
        if i > 0:
            inBodySlices.append({'z': bodyMin, 'polygon': polygonFromBody(bodyMin, bodyInfo['body'].volume, cutoff=POLYGON_CUTOFF)})
            length = (zLengths[i] - zLengths[i - 1]) / (bodyInfo['slices'][i]['z'] - bodyInfo['slices']
                                                        [i - 1]['z']) * (bodyMin - bodyInfo['slices'][i - 1]['z']) + zLengths[i - 1]
            newZ.append(length)
        j = i
        while j < len(bodyInfo['slices']) and bodyMax > bodyInfo['slices'][j]['z']:
            inBodySlices.append(bodyInfo['slices'][j])
            newZ.append(zLengths[j])
            j += 1

        if j < len(zLengths):
            length = (zLengths[j] - zLengths[j - 1]) / (bodyInfo['slices'][j]['z'] - bodyInfo['slices']
                                                        [j - 1]['z']) * (bodyMax - bodyInfo['slices'][j - 1]['z']) + zLengths[j - 1]
            newZ.append(length)
            inBodySlices.append({'z': bodyMax, 'polygon': polygonFromBody(bodyMax, bodyInfo['body'].volume)})

        totalZ = sum(newZ)
        allocations = newZ / totalZ * bodyInfo['body'].samples
        allocationsInt = np.floor(allocations).astype(np.int32)
        fracs = allocations - allocationsInt
        order = np.flip(np.argsort(fracs))
        allocated = np.sum(allocationsInt)
        for i in range(bodyInfo['body'].samples - allocated):
            allocationsInt[order[i % len(order)]] += 1
        for i in range(len(newZ)):
            yield allocationsInt[i], inBodySlices[i]['polygon'], inBodySlices[i]['z']

    def _sampleSlice(self, numPoints, polygon, z, group, visits):
        samples = []
        pointsIndex = 0
        remainingSamples = numPoints * self.headingStrategy.numHeadings * self.numPhi
        lr = remainingSamples
        i = 0
        while remainingSamples > 0 and i < LIMIT:
            points = getPointsOnEdge(pointsIndex + i, int(np.ceil(remainingSamples / (self.headingStrategy.numHeadings * self.numPhi))), polygon)
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
            if remainingSamples == lr:
                i += 1
            lr = remainingSamples
        return samples
