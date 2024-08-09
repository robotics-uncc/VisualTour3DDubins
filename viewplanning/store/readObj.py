import numpy as np
import pyvista as pv


def readObj(fileName, rotationMatrix=np.eye(3)) -> pv.PolyData:
    '''
    read meshes from a file and rotate them

    Parameters
    ----------
    fileName: str
        path to the mesh
    rotationMatrix: np.ndarray
        SO(3) to rotate the mesh with
    
    Returns
    -------
    pv.PolyData
        mesh
    '''
    reader = pv.get_reader(fileName)
    obj: pv.PolyData = reader.read()
    transform = np.eye(4)
    transform[:3, :3] = rotationMatrix
    obj = obj.transform(transform)
    obj = obj.triangulate()
    return obj
