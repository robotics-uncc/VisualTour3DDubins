from .Tsp import TspSolver
import networkx as nx
from .helpers import noonAndBeanTransforms
import uuid
from typing import Callable
from viewplanning.models import Vertex
import random


class NetworkXTsp(TspSolver):
    '''
    use networkX to solve a tsp with simulated annealing
    '''
    def __init__(self):
        self.graph: nx.DiGraph = None

    def writeFiles(self, id: uuid.UUID, vertices: 'list[Vertex]', cost: Callable[[Vertex, Vertex], float]):
        L = len(vertices)
        costMatrix = noonAndBeanTransforms(cost, vertices)
        self.graph = nx.DiGraph()
        self.graph.add_nodes_from(range(L))
        for i in range(L):
            for j in range(L):
                self.graph.add_edge(i, j, weight=costMatrix[i, j])

    def solve(self, id, vertices: 'list[Vertex]') -> 'list[Vertex]':
        cycle = list(range(len(vertices)))
        random.shuffle(cycle)
        cycle += [cycle[0]]
        path = [vertices[i] for i in nx.approximation.simulated_annealing_tsp(self.graph, cycle, max_iterations=100, N_inner=1000, temp=10, alpha=.1)]
        finalPath = []
        groups = set()
        for vertex in path:
            if vertex.group in groups:
                continue
            groups.add(vertex.group)
            finalPath.append(vertex)
        return finalPath
