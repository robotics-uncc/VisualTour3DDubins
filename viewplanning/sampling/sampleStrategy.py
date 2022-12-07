from typing import Generic, TypeVar, Iterator
from viewplanning.models import Vertex
import numpy as np

T = TypeVar('T')


class SampleStrategy(Generic[T]):
    def __init__(self) -> None:
        pass

    def getSamples(self, regions: 'Iterator[T]') -> 'list[Vertex]':
        pass
