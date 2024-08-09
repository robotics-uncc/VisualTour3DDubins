import numpy as np
from typing import Callable, Tuple
from viewplanning.models import Vertex
import networkx as nx


def noonAndBeanTransforms(costFunction: Callable[[Vertex, Vertex], float], vertices: 'list[Vertex]'):
    '''
    use the noon and bean transforms to transform a TSP with neighborhoods to a asymetric TSP
    '''
    L = len(vertices)
    costMatrix = -1 * np.ones([L, L])
    adjMatrixCostCalcs = np.zeros([L, L])
    groupDict: dict[str, list[Tuple[int, Vertex]]] = {}
    for i, vertex in enumerate(vertices):
        if vertex.group not in groupDict.keys():
            groupDict[vertex.group] = []
        groupDict[vertex.group].append((i, vertex))
    for group in groupDict.values():
        # intra-cluster arcs
        for j in range(len(group)):
            costMatrix[group[j - 1][0], group[j][0]] = 0
        # intra-cluster arc switching
        for i in range(len(group)):
            for j, vertex in enumerate(vertices):
                if group[i][1].group == vertex.group or group[i][1].id == vertex.id:
                    continue
                costMatrix[group[i - 1][0], j] = costFunction(group[i][1], vertex)
                adjMatrixCostCalcs[group[i - 1][0], j] = costFunction(group[i][1], vertex)

    totalCost = np.max(adjMatrixCostCalcs)
    beta = totalCost

    for i in range(L):
        for j in range(L):
            if costMatrix[i, j] != 0 and costMatrix[i, j] != -1:
                costMatrix[i, j] = (costMatrix[i, j] + beta) * 1000
                adjMatrixCostCalcs[i, j] = adjMatrixCostCalcs[i, j] + beta

    totalCost = np.sum(adjMatrixCostCalcs)

    beta2 = 5 * totalCost

    for i in range(L):
        for j in range(L):
            if costMatrix[i, j] == -1:
                costMatrix[i, j] = beta2

    return costMatrix
