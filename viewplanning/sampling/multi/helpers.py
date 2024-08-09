from typing import Callable, Any
from viewplanning.models import VertexMulti, Region
from viewplanning.store import MeshStore, IntersectionStore
from viewplanning.sampling.sampleHelpers import IdProvider, SamplingFailedException
import copy
import numpy as np
import networkx as nx
from networkx.algorithms import enumerate_all_cliques
from dataclasses import dataclass, field
import pyvista as pv
from viewplanning.sampling.heading import HeadingStrategy
import logging
import os
import pymeshfix as mf


APPROX_ZERO = 1e-3


@dataclass
class Volume:
    '''data structure for storing information about visibility volumes and their intersections'''
    parents: 'list[int]' = field(default_factory=list)
    volume: pv.PolyData = field(default=None)
    samples: int = 0
    value: float = 0


def checkMultiRegion(samples: 'list[VertexMulti]', meshes: 'list', contains: 'Callable[[list[float], Any], bool]'):
    '''
    checks if samples are in multiple visibility volumes and adds the samples to the other visibility volumes by duplicating the sample.
    mutates the samples list

    Parameters
    ----------
    samples: list[VertexMulti]
        a list of samples to check
    meshes: list
        a list of visibility volumes
    contains: (list[float], Any) -> bool
        a function to check if a sample is in a visiblity region
    
    Returns
    -------
    list[VertexMulti]
        an updated list of samples
    '''
    ids = IdProvider.getInsance('')
    j = 0
    length = len(samples)
    while j < length:
        sample = samples[j]
        sample.id = ids.getId()
        for i, mesh in enumerate(meshes):
            if i not in sample.visits and contains(sample.toList()[:3], mesh):
                sample.visits.add(str(i))

        queue = sample.visits.copy()
        # remove current group if it exists
        if sample.group in queue:
            queue.remove(sample.group)

        # continually make a copy of the node until there's a copy for all meshes
        while len(queue) > 0:
            newSample = copy.deepcopy(sample)
            newSample.group = queue.pop()
            samples.append(newSample)
        j += 1
    return samples


def makeDuplicateNodes(samples: 'list[VertexMulti]'):
    '''
    Duplicates nodes in multiple visiblity volumes so each volume has its own samples.
    Mutates the list of samples.

    Parameters
    ----------
    samples: list[VertexMulti]
        the list of samples
    '''
    ids = IdProvider.getInsance('')
    j = 0
    length = len(samples)
    while j < length:
        sample = samples[j]
        sample.id = ids.getId()

        queue = sample.visits.copy()
        # remove current group if it exists
        if sample.group in queue:
            queue.remove(sample.group)

        # continually make a copy of the node until there's a copy for all meshes
        while len(queue) > 0:
            newSample = copy.deepcopy(sample)
            newSample.group = queue.pop()
            samples.append(newSample)
        j += 1
    return samples


def makeGraph(regions: 'list[Region]', radius: float, dwell: float, multDwell=True):
    '''
    Makes a graph to check for intersections between visibility volumes.

    Parameters
    ----------
    regions: list[Region]
        a list of visibility volumes to check
    radius: float
        max viewing distance for the visibility volumes
    dwell: float
        how long in (length) to stay in the visiblity volumes
    multDwell:
        multiply dwell distance based on the number of visible targets
    '''
    graph = nx.Graph()
    queue = regions.copy()
    graph.add_nodes_from(range(len(regions)))
    i = 0
    while len(queue) > 0:
        current = queue.pop(0)
        j = i + 1
        for other in queue:
            if isEdge(current, other, radius, (dwell * 2) if multDwell else dwell):
                graph.add_edge(i, j)
            j += 1
        i += 1
    return graph


def isEdge(a: Region, b: Region, radius: float, dwell: float):
    '''
    is there an intersection between visiblity volumes

    Parameters
    ----------
    a: Region
        visiblity volumes a
    b: Region
        visibility volume b
    radius: float
        max sensing distance for the camera
    dwell: float
        distance to remain in the visibility volume
    '''
    aCenter = np.array(a.points[0])
    bCenter = np.array(b.points[0])
    d = np.linalg.norm(aCenter - bCenter)
    if d > radius * 2:
        return False
    mid = (aCenter + bCenter) / 2
    l = np.linalg.norm(mid - aCenter)
    r = np.sqrt(radius ** 2 - l ** 2)
    if r * 2 < dwell and (radius - l) * 2 < dwell:
        return False
    store = MeshStore.getInstance()
    aMesh = store.getMesh(a.file, a.rotationMatrix)
    bMesh = store.getMesh(b.file, b.rotationMatrix)
    ax0, ax1, ay0, ay1, az0, az1 = aMesh.bounds
    bx0, bx1, by0, by1, bz0, bz1 = bMesh.bounds
    if bx0 > ax1 or bx1 < ax0 or by0 > ay1 or by1 < ay0 or bz0 > az1 or bz1 < az0:
        return False
    interStore = IntersectionStore.getInstance()
    intersection = interStore.intersect(aMesh, bMesh, os.path.basename(a.file), os.path.basename(b.file))
    if intersection is None:
        return False
    x_min, x_max, y_min, y_max, _, _ = intersection.bounds
    if intersection.n_points <= 0:
        return False
    k = np.sqrt((x_max - x_min) ** 2 + (y_max - y_min) ** 2)
    return k > dwell


def findCliques(regions: 'list[Region]', radius: float, clique_limit: int = 3, dwell: float = 0, multDwell: bool = True):
    '''
    return a list of possible visibility volume intersections

    Parameters
    ----------
    regions: list[Region]
        a list of visibility volumes
    radius: float
        max sensing distance for the camera
    clique_limit: int = 3
        max clique number to consider
    dwell: float = 0
        dwell distance to remain in a visiblity volume
    multDwell: bool = True
        multipy the dwell distance by the number of visible targets
    
    Returns
    -------
    list[list[int]]
        a set of set of possible visibility volume intersections
    '''
    graph = makeGraph(regions, radius, dwell, multDwell)
    cliques = []
    for clique in enumerate_all_cliques(graph):
        if len(clique) <= clique_limit:
            cliques.append(clique)
        else:
            return cliques
    return cliques

class MultiSampleStrategy:
    '''
    A abstract class for method that consider the intersection of visibility volumes
    '''
    def __init__(self, numSamples: int, headingStrategy: HeadingStrategy):
        '''
        Parameters
        ----------
        numSamples: int
            number of (x, y, z) samples per visiblity volume
        headingStrategy: HeadingStrategy
            how to find heading angle(s) for each sample
        '''
        self.headingStrategy = headingStrategy
        self.numSamples = numSamples

    def sampleMeshes(self, volumes: 'list[Volume]', meshes: 'list[pv.PolyData]', regions: 'list[Region]') -> 'list[VertexMulti]':
        '''
        sample volumes and return a set of samples for the visbility volumes

        Parameters
        ----------
        volumes: list[Volume]
            a list of visiblity volumes or intersections of visiblity volumes to sample
        meshes: list[pv.PolyData]
            a list of visiblity volumes
        regions: list[Region]
            a list of regions to samples
        '''
        raise NotImplementedError()


