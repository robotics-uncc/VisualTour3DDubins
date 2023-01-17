from viewplanning.models import Vertex
from typing import Callable
import uuid
import numpy as np


class TspSolver:
    '''
    base class for TSP solvers
    '''

    def writeFiles(self, id: uuid.UUID, vertices: 'list[Vertex]', cost: Callable[[Vertex, Vertex], float]):
        '''
        write the files for GLKH to use

        Parameters
        ----------
        id: UUID
            id to disallow collision of experiments
        vertices: list[Vertex]
            list of vertices for TSP
        cost: Callable[[Vertex, Vertex], float]
            function to find cost from two vertices
        '''
        pass

    def solve(self, id, vertices: 'list[Vertex]') -> 'list[Vertex]':
        '''
        invoke GLKH and read result files

        Parameters
        ----------
        id: UUID
            id to disallow collision of experiments
        vertices: list[Vertex]
            list of vertices for TSP

        Returns
        -------
        ordered list of vertices that solves TSP
        '''
        pass

    def cleanUp(self, id):
        '''
        clean up resouces that where used to solve TSP

        Parameters
        ----------
        id: UUID
            id to disallow collision of experiments
        '''
        pass
