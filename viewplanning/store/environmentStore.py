import pyvista as pv
import numpy as np
import os


class EnvironmentStore:
    '''
    reads environments from files and caches them in memory
    '''
    __instance = None

    @staticmethod
    def getInstance():
        '''
        singleton creation method
        '''
        if EnvironmentStore.__instance is None:
            EnvironmentStore.__instance = EnvironmentStore()
        return EnvironmentStore.__instance

    def __init__(self) -> None:
        '''
        This class is designed as a singleton don't call this
        '''
        self.items = {}

    def getEnvironment(self, file, rotationMatrix):
        '''
        Read and transform the environment and store it in memory

        Parameters
        ----------
        file: str
            file path for the environment
        rotationMatrix: np.ndarray
            SO(3) element for rotating the environment
        '''
        if not os.path.exists(file):
            raise FileNotFoundError()
        if file in self.items.keys():
            return self.items[file]
        reader = pv.get_reader(file)
        environment: pv.PolyData = reader.read()
        transform = np.eye(4)
        transform[:3, :3] = rotationMatrix
        environment.transform(transform)
        self.items[file] = environment
        return environment
