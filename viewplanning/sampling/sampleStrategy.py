from typing import Generic, TypeVar, Iterator
from viewplanning.models import Vertex
from viewplanning.sampling.heading import HeadingStrategy


T = TypeVar('T')


class SampleStrategy(Generic[T]):
    '''
    Super class for the different sample stratgies.
    '''

    def __init__(self, headingStrategy: HeadingStrategy) -> None:
        self.headingStrategy = headingStrategy

    def getSamples(self, regions: 'Iterator[T]') -> 'list[Vertex]':
        '''
        Sample the regions

        Parameters
        ----------
        regions: Iterator[T]
            regions to sample

        Returns
        -------
        list[Vertex]
            list of sample points
        '''
        pass
