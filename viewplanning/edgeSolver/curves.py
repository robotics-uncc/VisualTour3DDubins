from viewplanning.models.edge import Edge, Edge3D, DwellStraightEdge, EdgeType, LeadInDwellEdge, Edge2D
from viewplanning.models.dubinsPathType import DubinsPathType
import numpy as np
from typing import Callable


def dwellStraightCurve(edge: DwellStraightEdge):
    """
    return a path function for a dubins curve with a straight segment at the start where the input t is in [0, 1]

    Paramters
    ---------
    path: DwellStraightEdge
        dwell straight edge

    Returns
    -------
    f(float) -> ndarray
        return mapping to 3d point in space
    """
    if edge.transitionEdge.type == EdgeType.THREE_D:
        dubins = vanaAirplaneCurve(edge.transitionEdge)
    else:
        dubins = dubinsCurve(edge.transitionEdge)

    def curve(t: float):
        dubinsCost = edge.transitionEdge.cost / edge.cost
        dwellCost = 1 - dubinsCost
        if t > dwellCost:
            return dubins((t - dwellCost) / dubinsCost)
        return edge.start.asPoint() + edge.dwellVector * (t / dwellCost)
    return curve


def leadInDwellCurve(edge: LeadInDwellEdge):
    """
    return a path function for a dubins curve with a straight segment at the start and end where the input t is in [0, 1]

    Paramters
    ---------
    path: LeadIndwellEdge
        lead in dwell edge

    Returns
    -------
    f(float) -> ndarray
        return mapping to 3d point in space
    """
    if edge.transitionEdge.type == EdgeType.THREE_D:
        dubins = vanaAirplaneCurve(edge.transitionEdge)
    else:
        dubins = dubinsCurve(edge.transitionEdge)

    def curve(t: float):
        dubinsCost = edge.transitionEdge.cost / edge.cost
        dwellCost = np.linalg.norm(edge.dwellVector) / edge.cost
        leadCost = np.linalg.norm(edge.leadVector) / edge.cost
        if t > dwellCost + dubinsCost:
            return edge.transitionEdge.end.asPoint() + edge.leadVector * ((t - dwellCost - dubinsCost) / leadCost)
        elif t > dwellCost:
            return dubins((t - dwellCost) / dubinsCost)
        return edge.start.asPoint() + edge.dwellVector * (t / dwellCost)
    return curve


def vanaAirplaneCurve(path: Edge3D) -> Callable[[float], np.ndarray]:
    """
    return a path function for a dubins curve where the input t is in [0, 1]

    Paramters
    ---------
    path: Edge3D
        vana dubins path

    Returns
    -------
    f(float) -> ndarray
        return mapping to 3d point in space
    """
    xyFunction = dubinsCurve2d([path.start.x, path.start.y, path.start.theta],
                               path.aParam, path.bParam, path.cParam, path.radius, path.pathType)
    szFunction = dubinsCurve2d([0, path.start.z, path.start.phi], path.dParam,
                               path.eParam, path.fParam, path.radiusSZ, path.pathTypeSZ)

    def f(t):
        xy = xyFunction(t)
        sz = szFunction(t)
        return np.append(xy, sz[1])
    return f


def dubinsCurve(edge: Edge2D):
    """
    return a path function for a dubins curve where the input t is in [0, 1]

    Paramters
    ---------
    path: Edge2D
        dubins path

    Returns
    -------
    f(float) -> ndarray
        return mapping to 3d point in space
    """
    return dubinsCurve2d(edge.start.toList(), edge.aParam, edge.bParam, edge.cParam, edge.radius, edge.pathType)


def dubinsCurve2d(s: np.ndarray, a, b, c, r, type: DubinsPathType):
    """
    return a path function for a dubins curve where the input t is in [0, 1]

    Parameters
    ----------
    s: np.ndarray
        starting point for the curve
    a: float
        dubins path a parameter
    b: float
        dubins path b parameter
    c: float
        dubins path c paramters
    r: float
        dubins path radius
    type: DubinsPathType
        dubins path type

    Returns
    -------
    (float) -> np.ndarray
        path function where input goes from 0 to 1
    """
    i = maneuverToDir(type.name[0])
    j = maneuverToDir(type.name[1])
    k = maneuverToDir(type.name[2])
    s1 = r * i * np.array([-np.sin(s[2]), np.cos(s[2])]) + s[:2] + r * \
        np.array([np.cos(i * a / r + s[2] - i * np.pi / 2),
                 np.sin(i * a / r + s[2] - i * np.pi / 2)])
    h1 = i * a / r + s[2]
    if j == 0:
        s2 = s1 + b * np.array([np.cos(h1), np.sin(h1)])
        h2 = h1
    else:
        s2 = s1 + r * j * np.array([-np.sin(h1), np.cos(h1)]) + r * np.array(
            [np.cos(j * b / r + h1 - j * np.pi / 2), np.sin(j * b / r + h1 - j * np.pi / 2)])
        h2 = h1 + j * b / r

    def f(t):
        t = t * (a + b + c)
        if t < a:
            p0 = r * i * np.array([-np.sin(s[2]), np.cos(s[2])])
            p1 = s[:2]
            p2 = r * np.array([np.cos(i * t / r + s[2] - i * np.pi / 2),
                              np.sin(i * t / r + s[2] - i * np.pi / 2)])
            return p0 + p1 + p2
        if t >= a and t < a + b and j == 0:
            u = t - a
            return s1 + u * np.array([np.cos(h1), np.sin(h1)])
        if t >= a and t < a + b:
            u = t - a
            p0 = r * j * np.array([-np.sin(h1), np.cos(h1)])
            p1 = s1
            p2 = r * np.array([np.cos(j * u / r + h1 - j * np.pi / 2),
                              np.sin(j * u / r + h1 - j * np.pi / 2)])
            return p0 + p1 + p2
        u = t - b - a
        p0 = r * k * np.array([-np.sin(h2), np.cos(h2)])
        p1 = s2
        p2 = r * np.array([np.cos(k * u / r + h2 - k * np.pi / 2),
                          np.sin(k * u / r + h2 - k * np.pi / 2)])
        return p0 + p1 + p2

    return f


def maneuverToDir(str: str) -> int:
    """
    maps dubins curve action to an interger {-1, 0, 1}

    Paramters
    ---------
    str: str
        dubins curve action

    Returns
    -------
    int
        L -> 1, R -> -1, S -> 0
    """
    if str == 'L':
        return 1
    if str == 'R':
        return -1
    return 0


def makeCurve(edge: Edge, n=100):
    '''
    make a array of size [n, d] points for an edge

    Parameters
    ----------
    edge: Edge
        edge to make a curve for
    n: int
        number of point along the curve

    Returns
    -------
    np.ndarray
    '''
    if edge.type == EdgeType.TWO_D:
        f = dubinsCurve(edge)
    elif edge.type == EdgeType.THREE_D:
        f = vanaAirplaneCurve(edge)
    elif edge.type == EdgeType.DWELL_STRAIGHT:
        f = dwellStraightCurve(edge)
    elif edge.type == EdgeType.LEAD_IN_DWELL:
        f = leadInDwellCurve(edge)
    else:
        raise NotImplementedError(f'Edge Type {edge.type} is not implemeted')

    return np.row_stack([f(t) for t in np.linspace(0, 1, n)])
