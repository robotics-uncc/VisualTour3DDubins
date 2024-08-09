import numpy as np
from shapely.geometry.polygon import Polygon
from dataclasses import dataclass


APPROX_ZERO = 1e-4
TWO_PI = 2 * np.pi


def dwellHeadingSubsets(point: np.ndarray, polygon: Polygon, numRays: int, dwellDistance: float):
    '''
    find  set of valid heading angles for a point polygon pair with a dwellDistance

    Parameters
    ----------
    point: np.ndarray
        point where the headings are tested
    polygon: Polygon
        a horizontal slice of a visiblity polygon
    numRays: int
        numer of rays to test headings with
    dwellDistance: float
        how far in a heading direction the vehicle needs to dwell in visiblility volume
    
    Returns
    -------
    list[list]
        a set of subsets of valid heading angles
    '''
    s = getSegment(point, polygon)
    d = s[1, :] - s[0, :]
    theta0 = np.arctan2(d[1], d[0])
    theta = np.linspace(theta0, theta0 + np.pi, numRays)
    ray = np.row_stack([np.cos(theta), np.sin(theta)]).T
    distances = intersectRays([polygon], point, ray, np.inf)
    valid = distances > dwellDistance
    sets = []
    current = None
    for i in range(valid.shape[0]):
        if valid[i] and current is None:
            current = i
        elif not valid[i] and current is not None:
            sets.append((theta[current], theta[i - 1]))
            current = None
    if current is not None:
        sets.append((theta[current], theta[valid.shape[0] - 1]))
    return sets


def getSegment(point: np.ndarray, polygon: Polygon):
    '''
    gets the segment on a polygon closest to a point

    Parameters
    ----------
    point: np.ndarray
        point to test
    polygon: Polygon
        polygon to find segment on
    
    Returns
    -------
    np.ndarray
        a pair of points representing a line segment
    '''
    vertices = np.array(polygon.exterior.coords[:-1])
    d = np.roll(vertices, -1, 0) - vertices
    p = vertices - point
    d = d[:, :2]
    p = p[:, :2]
    t = np.cross(d, p, axis=1)
    i = np.argmin(np.abs(t))
    if i + 2 > vertices.shape[0]:
        return np.row_stack([vertices[i], vertices[0]])
    return vertices[i:i + 2, :]


def intersectRays(polygons: 'list[Polygon]', start: np.ndarray, dirs: np.ndarray, dmax: float):
    '''
    ray traces from a start point in dirs direction to dmax. The rays intersect the polygons

    Parameters
    ----------
    polygons: list[Polygon]
        objects to block the rays
    start: np.ndarray
        start point
    dirs: np.ndarray
        directions to emit the rays
    dmax: float
        maximum distance to consider
    
    Returns
    -------
    np.ndarray
        a set of distances where the rays intersect or dmax if no intersection
    '''
    dirs = np.apply_along_axis(lambda x: x / np.linalg.norm(x), 1, dirs)
    s0hat = []
    nhat = []
    s1hat = []
    for polygon in polygons:
        t0 = np.array(polygon.exterior.coords[:-1])[:, :2]
        t1 = np.roll(t0, 1, 0)
        nhat.append(t1 - t0)
        s0hat.append(t0)
        s1hat.append(t1)
    s0 = np.row_stack(s0hat)
    s1 = np.row_stack(s1hat)
    n = np.row_stack(nhat)
    p = np.matmul(dirs, [[0, 1], [-1, 0]])
    nom = np.einsum('kj, ij -> ik', p, s0 - start[:2])
    denom = np.einsum('kj, ij -> ik', p, n)
    with np.errstate(divide='ignore'):
        t = -nom / denom
    # get rid of points not on line segments
    t[t < -APPROX_ZERO] = np.inf
    t[t > 1 + APPROX_ZERO] = np.inf
    points = np.zeros([t.shape[0], t.shape[1], 2])
    with np.errstate(invalid='ignore'):
        for ii in range(t.shape[0]):
            for jj in range(t.shape[1]):
                points[ii, jj, :] = t[ii, jj] * n[ii] + s0[ii]

    vectors = points - np.reshape(start[:2], [1, 1, 2])
    distance = np.einsum('kj, ikj -> ik', dirs, vectors)
    # ensure ray is going the right direction and limit direction
    distance[distance < 0] = dmax
    distance[distance > dmax] = dmax
    distance[np.isnan(distance)] = dmax
    index = np.argmin(distance, axis=0)

    return np.squeeze([distance[index[i], i] for i in range(index.shape[0])])
