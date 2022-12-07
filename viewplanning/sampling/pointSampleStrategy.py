from typing import Iterator
from viewplanning.sampling.sampleStrategy import SampleStrategy
from viewplanning.models import Region, Vertex2D
from viewplanning.sampling.sampleHelpers import iterateRegions
import numpy as np

class PointSampleStrategy(SampleStrategy[Region]):
    def __init__(self, numTheta):
        super().__init__()
        self.numTheta = numTheta

    def getSamples(self, regions:'Iterator[Region]') -> 'list[Vertex2D]':
        samples = []
        for group, points in enumerate(iterateRegions(regions)):
            for point in points:
                for i in range(self.numTheta):
                    samples.append(Vertex2D(group=str(group), x=point[0], y=point[1], theta=i * 2 * np.pi / self.numTheta))
        return samples