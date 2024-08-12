import numpy as np
from shapely.geometry.polygon import Polygon, orient
from viewplanning.models import Region, RegionType
from viewplanning.store import readObj
import pyvista as pv
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider

APPROX_ZERO = 1e-4
DUPLICATE_MAG_CUTOFF = 1e-4
DZ_MAX = .01


class SamplingFailedException(Exception):
    pass


def iterateRegions(regions: 'list[Region]', type=RegionType.UNKNOWN):
    '''
    Reads representations regions into memory.

    Parameters
    ----------
    regions: list[Region]
        list of regions to read
    type: RegionType
        force a region to be a specific type

    Returns
    -------
    Generator[list[Polygon] | list[pv.PolyData] | list[list[float]]]
        Representation of the region
    '''
    for region in regions:
        if type == RegionType.UNKNOWN:
            if region.type == RegionType.POINT:
                yield region.points
            elif region.type == RegionType.POLYGON:
                mesh = readObj(region.file, region.rotationMatrix)
                _, _, _, _, minZ, maxZ = mesh.bounds
                dz = maxZ - minZ
                z = region.z
                polygon = None
                while polygon is None and z < region.z + dz * DZ_MAX:
                    polygon = polygonFromBody(z, mesh)
                    z += .1
                yield polygon
            elif region.type == RegionType.WAVEFRONT:
                obj = readObj(region.file, region.rotationMatrix)
                if obj.n_cells > 0:
                    yield obj
            elif region.type == RegionType.WAVEFRONT_VRIO:
                obj = readObj(region.file, region.rotationMatrix)
                if obj.n_cells > 0:
                    yield obj
        else:
            if type == RegionType.POINT:
                yield region.points
            elif type == RegionType.POLYGON:
                yield polygonFromBody(region.z, readObj(region.file, region.rotationMatrix))
            elif type == RegionType.WAVEFRONT:
                obj = readObj(region.file, region.rotationMatrix)
                if obj.n_cells > 0:
                    yield obj
            elif type == RegionType.WAVEFRONT_VRIO:
                obj = readObj(region.file, region.rotationMatrix)
                if obj.n_cells > 0:
                    yield obj


class Node:
    """
        node class for connecting line segments
    """

    def __init__(self, start, end):
        self.start = start
        self.end = end


def polygonFromBody(zLevel: float, mesh: pv.PolyData, cutoff=APPROX_ZERO, debug=False) -> Polygon:
    """
    slices a mesh along a plane parallel to xy plane at height zLevel and returns the largest polygon.

    Parameters
    ----------
    zLevel: float
        z height to slice at
    mesh: Obj
        environment mesh
    Returns
    -------
    Polygons
        polygon resulting from z slice
    """
    polygon: Polygon = None
    if mesh.bounds[4] > zLevel or mesh.bounds[5] < zLevel:
        return None
    for p in polygonsFromMesh(zLevel, mesh, cutoff=cutoff, debug=debug):
        if polygon is None or p.area > polygon.area:
            polygon = p
    return polygon


def polygonsFromMesh(zLevel: float, mesh: pv.PolyData, cutoff: float = APPROX_ZERO, debug=False) -> 'list[Polygon]':
    """
    slices a mesh along a plane parallel to xy plane at height zLevel

    Parameters
    ----------
    zLevel: float
        z height to slice at
    mesh: Obj
        environment mesh
    Returns
    -------
    list[Polygons]
        list of polygons resulting from z slice
    """
    # hist = []
    # k = 0
    points = np.array(mesh.points[mesh.faces.reshape(-1, 4)[:, 1:]])
    vectors = np.roll(points, 1, axis=1) - points
    with np.errstate(divide='ignore', invalid='ignore'):
        t = np.einsum('k, ijk->ij', [0, 0, 1], np.subtract(points, np.array(
            [[0, 0, zLevel]]))) / np.einsum('ijk, k->ij', -vectors, [0, 0, 1])
    indexLine = np.sum((t > 0) & (t < 1), axis=1) > 1
    intersections = np.sum(indexLine)
    indexIntersection = (t[indexLine] > 0) & (t[indexLine] < 1)
    p = np.reshape(points[indexLine][indexIntersection], [intersections, 2, 3])
    d = np.reshape(vectors[indexLine][indexIntersection], [
                   intersections, 2, 3])
    s = np.reshape(t[indexLine][indexIntersection], [intersections, 2])
    segments = np.zeros_like(p)
    for ii in range(p.shape[0]):
        for jj in range(p.shape[1]):
            segments[ii, jj, :] = p[ii, jj, :] + s[ii, jj] * d[ii, jj, :]
    # make polygons out of segments
    if len(segments) <= 0:
        return []
    ring = [Node(segments[0, 1, :].copy(), segments[0, 0, :].copy())]
    segments[0, :, :] = np.inf
    rings = []
    misses = 0
    while not np.isinf(segments).all():
        vec = np.linalg.norm(segments - ring[-1].end, axis=2)
        i = np.argmin(vec, axis=0)
        # check for duplicate segment
        a = vec[i, [0, 1]] < cutoff
        if i[0] == i[1] and a.all():
            segments[i] = np.inf
            continue

        # if the end matches
        if a.any():
            misses = 0
            if a[0]:
                segment = segments[i[0], :, :].copy()
                ring.append(Node(segment[0, :], segment[1, :]))
                segments[i[0], :, :] = np.inf
            else:
                segment = segments[i[1], :, :].copy()
                ring.append(Node(segment[1, :], segment[0, :]))
                segments[i[1], :, :] = np.inf

            # check to see if loop closed
            if np.linalg.norm(ring[0].start - ring[-1].end) < cutoff:
                rings.append(ring)
                if not np.isinf(segments).all():
                    i, _, _ = np.where(~np.isinf(segments))
                    ring = [Node(segments[i[0], 1, :].copy(),
                                 segments[i[0], 0, :].copy())]
                    segments[i[0], :, :] = np.inf
        else:
            misses += 1

        if misses > 0 and not np.isinf(segments).all():
            # bad ring
            if len(ring) > 1:
                # try again without last segment
                ring.pop()
            else:
                i, _, _ = np.where(~np.isinf(segments))
                ring = [Node(segments[i[0], 1, :].copy(),
                             segments[i[0], 0, :].copy())]
                segments[i[0], :, :] = np.inf
    # plotting debugging
    #     hist.append((segments.copy(), ring.copy()))
    #     k += 1
    # if debug:
    #     fig = plt.figure()
    #     ax = fig.add_subplot()

    #     def update(k):
    #         ax.clear()
    #         if k > len(hist):
    #             return
    #         for segment in hist[k][0]:
    #             ax.set_title(k)
    #             ax.plot(segment[:, 0], segment[:, 1])
    #         path = [hist[k][1][0].start]
    #         for segment in hist[k][1]:
    #             path.append(segment.end)
    #         path = np.array(path)
    #         ax.plot(path[:, 0], path[:, 1], marker='x', color='m')

    #     fig.subplots_adjust(left=0.25, bottom=0.25)
    #     sAx = fig.add_axes([0.25, 0.1, 0.65, 0.03])
    #     slider = Slider(sAx, 'step', 0, len(hist) - 1, 0, valstep=1)
    #     slider.on_changed(update)
    #     # ani = FuncAnimation(fig, update, frames=range(len(hist)), blit=False)
    #     plt.show()
    polygons = []
    for ring in rings:
        ps = []
        for current in ring:
            if np.linalg.norm(current.start - current.end) > cutoff:
                ps.append(current.start)
        ps.append(current.end)
        if len(ps) < 3:
            continue
        polygon = np.array(orient(Polygon(shell=ps)).exterior.coords)[:-1]
        theta = (np.arctan2(polygon[:, 1],
                 polygon[:, 0]) + 2 * np.pi) % (2 * np.pi)
        index = np.argmin(theta)
        polygon = np.roll(polygon, -index, axis=0)
        polygons.append(Polygon(polygon))

    return polygons


def containsPoint2d(point, polygon: Polygon):
    '''
    Determines if a 2D polygon containts a point.

    Parameters
    ----------
    point: list
        (x,y) point
    polygon: Polygon
        polygon to text

    Returns
    -------
    bool
        True, if the point is in the polygon.
        False, if the point is not in the polygon.
    '''
    x0, y0, x1, y1 = polygon.bounds
    ty = point[1]
    tx = point[0]
    if (x0 - tx) * (x1 - tx) > -APPROX_ZERO:
        return False
    if (y0 - ty) * (y1 - ty) > - APPROX_ZERO:
        return False
    vertices1 = np.array(polygon.exterior.xy).T[:-1, :]
    vertices = np.roll(vertices1, 1, axis=0)
    yFlag = vertices[:, 1] >= ty
    yFlag1 = vertices1[:, 1] >= ty
    p = vertices[yFlag != yFlag1]
    p1 = vertices1[yFlag != yFlag1]
    f = yFlag1[yFlag != yFlag1]
    a = (p1[:, 1] - ty) * (p[:, 0] - p1[:, 0])
    b = (p1[:, 0] - tx) * (p[:, 1] - p1[:, 1])
    t = ((a >= b) == f)
    return np.sum(t) % 2 == 1


def containsPoint3d(point, body: pv.PolyData):
    '''
    Determines if a 3D volume containts a point by breaking it into a 2D polygon and testing the polygon.

    Parameters
    ----------
    point: list
        (x,y) point
    body: pv.PolyData
        3D volume to test

    Returns
    -------
    bool
        True, if the point is in the volume.
        False, if the point is not in the volume.
    '''
    # check boudning box
    x0, x1, y0, y1, z0, z1 = body.bounds
    tz = point[2]
    ty = point[1]
    tx = point[0]
    if (x0 - tx) * (x1 - tx) > -APPROX_ZERO:
        return False
    if (y0 - ty) * (y1 - ty) > - APPROX_ZERO:
        return False
    if (z0 - tz) * (z1 - tz) > - APPROX_ZERO:
        return False

    # use 2d method
    polygon = polygonFromBody(point[2], body)
    if polygon is None:
        return False

    return containsPoint2d(point[:2], polygon)


class IdProvider:
    '''
    Provides a unique integer id when called. IdProviders are given a name to reterive the provider from the global namespace.
    '''
    __instances = {}

    @staticmethod
    def getInsance(name: str) -> 'IdProvider':
        if name not in IdProvider.__instances.keys():
            IdProvider.__instances[name] = IdProvider()
        return IdProvider.__instances[name]

    def delInstance(name: str):
        IdProvider.__instances.pop(name)

    def __init__(self):
        self.i = 0

    def getId(self):
        j = self.i
        self.i += 1
        return j


def getAngle(i):
    '''
        Get a unique number between 0 and 2 not inclusive in the pattern 0, 1, .5, 1.5, .25, .75, 1.25, 1.75 ...

    Parameters
    ----------
    i: int
        index into the sequence

    Returns
    -------
    float
    '''
    if i == 0:
        return 0
    if i == 1:
        return 1
    j = i - 2
    n = 1
    while j >= sum([2 ** (s + 1) for s in range(n)]):
        n += 1
    k = j - sum([2 ** (s + 1) for s in range(n - 1)])
    return (2 * k + 1) / (2 ** n)


def getPointsOnEdge(startIndex: int, numPoints: int, polygon: Polygon):
    '''
    gets points on the edge of a polygon based on arclength of the polygon and the sequence [getAngle(startIndex), ... getAngle(startIndex + numPoints)]

    Parameters
    ----------
    startIndex: int
        offset into the getAngle sequence
    numPoints: int
        number of point along the polygon to return
    polygon: Polygon
        the polygon who's perimeter to place points on

    Returns
    -------
    list[float]
    '''
    fracs = [getAngle(i) / 2 for i in range(startIndex,
                                            startIndex + numPoints)]
    fracs.sort()
    perimeter = polygon.exterior.length
    segments = np.array(polygon.exterior.coords)
    j = 0
    travelDistance = 0
    a = segments[j + 1] - segments[j]
    d = np.linalg.norm(a)
    points = []
    for frac in fracs:
        # advance to line where next point is in the middle of
        while travelDistance < frac * perimeter:
            a = segments[j + 1] - segments[j]
            d = np.linalg.norm(a)
            travelDistance += d
            j += 1
        t = travelDistance - frac * perimeter
        point = segments[j] - t * a / np.linalg.norm(a)
        points.append(point)
    return points
