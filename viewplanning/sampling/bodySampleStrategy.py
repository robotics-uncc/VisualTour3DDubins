from typing import Iterator
import numpy as np
import random
from viewplanning.sampling.sampleStrategy import SampleStrategy
from viewplanning.sampling.sampleHelpers import containsPoint2d, polygonFromBody, iterateRegions
from viewplanning.models import Region, Vertex3D


class BodySampleStrategy(SampleStrategy[Region]):
    '''
    Body sample strategy samples points on the interior of a 3D volume. 
    Headings are sampled uniformly and pitches are sample uniformly between the supplied range.
    '''

    def __init__(self, numSamples, numTheta, numPhi, phiRange: 'list[float]'):
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
        self.numSamples = numSamples
        self.numTheta = numTheta
        self.numPhi = numPhi
        self.phiRange = phiRange

    def getSamples(self, bodies: Iterator[Region]) -> 'list[Vertex3D]':
        samples = []
        group = 0
        for body in iterateRegions(bodies):
            _, _, _, _, zMin, zMax = body.bounds
            while len(samples) < self.numSamples * self.numPhi * self.numTheta:
                z = random.random() * (zMax - zMin) + zMin
                polygon = polygonFromBody(z, body)
                while not polygon:
                    z = random.random() * (zMax - zMin) + zMin
                    polygon = polygonFromBody(z, body)
                xMin, yMin, xMax, yMax = polygon.bounds
                x = random.random() * (xMax - xMin) + xMin
                y = random.random() * (yMax - yMin) + yMin
                while not containsPoint2d([x, y, z], polygon):
                    x = random.random() * (xMax - xMin) + xMin
                    y = random.random() * (yMax - yMin) + yMin
                phiMag = self.phiRange[1] - self.phiRange[0]
                for i in range(self.numTheta):
                    for j in range(self.numPhi):
                        samples.append(Vertex3D(
                            group=str(group),
                            x=x,
                            y=y,
                            z=z,
                            theta=i * 2 * np.pi / self.numTheta,
                            phi=self.phiRange[0] + phiMag * j / self.numPhi
                        ))
            group += 1
        return samples
