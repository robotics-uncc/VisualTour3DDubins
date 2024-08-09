from typing import Iterator
from viewplanning.sampling.sampleStrategy import SampleStrategy
from viewplanning.models import Region, Vertex2D, RegionType
from viewplanning.sampling.sampleHelpers import iterateRegions
from viewplanning.sampling.heading import HeadingStrategy
import numpy as np


class PointSampleStrategy(SampleStrategy[Region]):
    '''
    Samples the point above the target with a uniform neighborhoods of heading angles.
    '''
    def __init__(self, headingStrategy: HeadingStrategy):
        '''
        Parameters
        ----------
        headingStrategy: HeadingStrategy
            how to allocate headings to the samples theta
        '''
        super().__init__(headingStrategy)

    def getSamples(self, regions: 'Iterator[Region]') -> 'list[Vertex2D]':
        samples = []
        for group, points in enumerate(iterateRegions(regions, type=RegionType.POINT)):
            for point in points:
                for theta in self.headingStrategy.getHeadings(point):
                    samples.append(Vertex2D(group=str(group), x=point[0], y=point[1], theta=theta))
        return samples
