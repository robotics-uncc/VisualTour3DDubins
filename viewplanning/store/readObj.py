import numpy as np
import pyvista as pv

def readObj(fileName, rotationMatrix=np.eye(3)) -> pv.PolyData:
    reader = pv.get_reader(fileName)
    obj: pv.PolyData = reader.read()
    transform = np.eye(4)
    transform[:3,:3] = rotationMatrix
    obj.transform(transform)
    return obj
