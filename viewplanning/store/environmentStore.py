import pyvista as pv
import numpy as np
import os
import logging


CACHE_SIZE = 50

class MeshStore:
    '''
    store meshes in a memory cache
    '''
    __instance: 'dict[int, MeshStore]' = {}

    @staticmethod
    def getInstance():
        '''get a mesh store for the current process'''
        pid = os.getpid()
        if pid not in MeshStore.__instance:
            MeshStore.__instance[pid] = MeshStore()
        return MeshStore.__instance[pid]

    def __init__(self) -> None:
        self.items = {}
        self.queue = []


    def getMesh(self, file, rotationMatrix):
        '''
        get a mesh from a file and rotate it with the rotation matrix

        Parameters
        ----------
        file: str
            path to mesh file
        rotationMatrix: np.ndarray
            SO(3) to rotate the mesh with
        '''
        if not os.path.exists(file):
            raise FileNotFoundError()
        if file in self.items.keys():
            return self.items[file]
        if len(self.queue) >= CACHE_SIZE:
            logging.debug('popping mesh cache')
            key = self.queue.pop()
            self.items.pop(key)

        reader = pv.get_reader(file)
        environment: pv.PolyData = reader.read()
        transform = np.eye(4)
        transform[:3, :3] = rotationMatrix
        environment.transform(transform)
        environment = environment.triangulate()
        self.items[file] = environment
        self.queue.append(file)
        return environment

    def clearCache(self):
        '''
        empty the store's cache of meshes
        '''
        self.queue.clear()
        self.items.clear()
