import pyvista as pv
import numpy as np
import os


class EnvironmentStore:
    __instance = None
    @staticmethod
    def getInstance():
        if EnvironmentStore.__instance is None:
            EnvironmentStore.__instance = EnvironmentStore()
        return EnvironmentStore.__instance
    
    def __init__(self) -> None:
        self.items = {}
    
    def getEnvironment(self, file, rotationMatrix):
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

