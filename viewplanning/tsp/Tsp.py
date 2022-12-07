from viewplanning.models import Vertex
from typing import Callable
import uuid
import numpy as np

class TspSolver:
    def writeFiles(self, id: uuid.UUID, vertices: 'list[Vertex]', cost: Callable[[Vertex, Vertex], float]):
        pass
    def solve(self, id, vertices: 'list[Vertex]') -> 'list[Vertex]':
        pass
    def cleanUp(self, id):
        pass