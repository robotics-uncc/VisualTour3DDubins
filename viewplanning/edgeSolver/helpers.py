from viewplanning.models import Edge, Edge3D, DwellStraightEdge, EdgeType, LeadInDwellEdge, Edge2D, DubinsPathType
import numpy as np
import pyvista as pv
from viewplanning.edgeSolver.curves import makeCurve

SEGMENTS = 10


def traceEdge(edge: Edge, environment: pv.PolyData):
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
    f = makeCurve(edge)
    points = np.array([f(t) for t in np.linspace(0, 1, SEGMENTS)])
    directions = np.roll(points, axis=0) - directions
    _, _, cells = environment.multi_ray_trace(points[:-1], directions[:-1], retry=True)
    if len(cells) > 0:
        return False
    return True
