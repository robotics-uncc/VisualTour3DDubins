from viewplanning.models import Edge3D
from viewplanning.plotting import makePath3d
import numpy as np
import pyvista as pv

SEGMENTS = 10


def traceEdge(edge: Edge3D, environment: pv.PolyData):
    '''
    traces edge to see if it collides with the environment

    Parameters
    ----------
    edge: Edge3D
        edge to trace
    environment: pv.PolyData
        environment to check for collisions

    Returns
    -------
    bool
        false if there is a collision true if no collision
    '''
    x, y, z = makePath3d(edge, n=SEGMENTS)
    points = np.column_stack((x, y, z))
    directions = np.roll(points, axis=0) - directions
    _, _, cells = environment.multi_ray_trace(points[:-1], directions[:-1], retry=True)
    if len(cells) > 0:
        return False
    return True
