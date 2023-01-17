import numpy as np
import pyvista as pv


def readObj(fileName, rotationMatrix=np.eye(3)) -> pv.PolyData:
    '''
    read a 3d mesh from a file

    Parameters
    ----------
    fileName: str
        file path of the mesh
    rotationMatrix: np.ndarray
        SO(3) matrix to rotating the mesh
    '''
    reader = pv.get_reader(fileName)
    obj: pv.PolyData = reader.read()
    transform = np.eye(4)
    transform[:3, :3] = rotationMatrix
    obj.transform(transform)
    return obj
