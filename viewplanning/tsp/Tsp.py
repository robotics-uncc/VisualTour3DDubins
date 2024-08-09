from viewplanning.models import Vertex
from typing import Callable
import uuid
import numpy as np


class TspSolver:
    '''
    solve a tsp
    '''
    def writeFiles(self, id: uuid.UUID, vertices: 'list[Vertex]', cost: Callable[[Vertex, Vertex], float]):
        '''
        write any necessary file to sovle the tsp

        Parameters
        ----------
        id: uuid.UUID
            id to gaurentee that files don\'t get overwritten
        vertices: list[Vertex]
            list of vertices to consider for the tsp
        cost: (Vertex, Vertex) -> float
            const function between to vertices
        '''
        pass

    def solve(self, id, vertices: 'list[Vertex]') -> 'list[Vertex]':
        '''
        solve the tsp

        Parameters
        ----------
        id: uuid.UUID
            id to gaurentee thet files don\'t get overwritten
        vertices: list[Vertex]
            list of vertices in the tsp
        
        Returns
        -------
        list[Vertex]
            solution to the tsp
        '''
        pass

    def cleanUp(self, id):
        '''
        cleanup any files leftover by the tsp solver

        Parameters
        ----------
        id: uuid.UUID
            id to gaurentee that files don\'t get overwritten
        '''
        pass
