from typing import Iterator
import numpy as np
import random
from viewplanning.sampling.sampleStrategy import SampleStrategy
from viewplanning.sampling.sampleHelpers import containsPoint2d, polygonFromBody, iterateRegions, SamplingFailedException
from viewplanning.models import Region, Vertex3D
from viewplanning.sampling.heading import HeadingStrategy
import pyvista as pv


class BodySampleStrategy(SampleStrategy[Region]):
    '''
    Body sample strategy samples points on the interior of a 3D volume. 
    Pitches are sample uniformly between the supplied range.
    '''
    def __init__(self, numSamples, numPhi, phiRange: 'list[float]', headingStrategy: HeadingStrategy):
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
    
    def getSamples(self, bodies: Iterator[Region]) -> 'list[Vertex3D]':
        samples = []
        group = 0
        for body in iterateRegions(bodies):
            body: pv.PolyData
            zMax = body.bounds[4]
            zMin = body.bounds[5]
            k = 0
            while k < self.numSamples * self.numPhi * self.headingStrategy.numHeadings:
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
                for theta in self.headingStrategy.getHeadings(np.array([x, y, z]), [0, 2 * np.pi], polygon=polygon):
                    for j in range(self.numPhi):
                        samples.append(Vertex3D(
                            group=str(group),
                            x=x,
                            y=y,
                            z=z,
                            theta=theta,
                            phi=self.phiRange[0] + phiMag * j / self.numPhi
                        ))
                        k += 1
                if k <= 0:
                    raise SamplingFailedException('Sample points failed to intersect with body')
            group += 1
        return samples
