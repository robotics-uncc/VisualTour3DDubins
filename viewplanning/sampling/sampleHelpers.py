import numpy as np
from shapely.geometry.polygon import Polygon, orient
from viewplanning.models import Region, RegionType
from viewplanning.store import readObj
import pyvista as pv

APPROX_ZERO = 1e-4
DUPLICATE_MAG_CUTOFF = 1e-4
DZ_MAX = .1


class SamplingFailedException(Exception):
    pass


def iterateRegions(regions: 'list[Region]', type=RegionType.UNKNOWN):

    for region in regions:
        if type == RegionType.UNKNOWN:
            if region.type == RegionType.POINT:
                yield region.points
            elif region.type == RegionType.POLYGON:
                mesh = readObj(region.file, region.rotationMatrix)
                _, _, _, _, zMin, zMax = mesh.bounds
                dz = zMax - zMin
                z = region.z + .01 * dz
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
        self.next: Node = None
        self.root: Node = None


def polygonFromBody(zLevel: float, mesh: pv.PolyData) -> Polygon:
    polygon: Polygon = None
    for p in polygonsFromMesh(zLevel, mesh):
        if polygon is None or p.area > polygon.area:
            polygon = p
    return polygon


def polygonsFromMesh(zLevel: float, mesh: pv.PolyData) -> 'list[Polygon]':
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
    points = np.array([mesh.cell_points(i) for i in range(mesh.n_cells)])
    vectors = np.roll(points, 1, axis=1) - points
    t = np.einsum('k, ijk->ij', [0, 0, 1],
                  np.subtract(points, np.array([[0, 0, zLevel]]))) / np.einsum('ijk, k->ij', -vectors, [0, 0, 1])
    indexLine = np.sum((t > 0) & (t < 1), axis=1) > 1
    # indexLine = np.sum((t >= 0) & (t < 1), axis=1) > 1
    intersections = np.sum(indexLine)
    indexIntersection = (t[indexLine] > 0) & (t[indexLine] < 1)
    p = np.reshape(points[indexLine][indexIntersection], [intersections, 2, 3])
    d = np.reshape(vectors[indexLine][indexIntersection], [intersections, 2, 3])
    s = np.reshape(t[indexLine][indexIntersection], [intersections, 2])
    segments = np.zeros_like(p)
    for ii in range(p.shape[0]):
        for jj in range(p.shape[1]):
            segments[ii, jj, :] = p[ii, jj, :] + s[ii, jj] * d[ii, jj, :]

    # make polygons out of segments
    if len(segments) <= 0:
        return []
    ring = Node(segments[0, 1, :].copy(), segments[0, 0, :].copy())
    segments[0, :, :] = np.inf
    rings = []
    while not np.isinf(segments).all():
        miss = True
        vec = np.linalg.norm(segments - ring.end, axis=2)
        i = np.argmin(vec, axis=0)
        # check for duplicate segment
        a = vec[i, [0, 1]] < APPROX_ZERO
        if i[0] == i[1] and a.all():
            segments[i] = np.inf
            miss = False
            continue

        # if the end matches
        if a.any():
            miss = False
            if a[0]:
                segment = segments[i[0], :, :].copy()
                ring.next = Node(segment[0, :], segment[1, :])
                segments[i[0], :, :] = np.inf
            else:
                segment = segments[i[1], :, :].copy()
                ring.next = Node(segment[1, :], segment[0, :])
                segments[i[1], :, :] = np.inf
            if ring.root is None:
                ring.next.root = ring
            else:
                ring.next.root = ring.root
            ring = ring.next

            # check to see if loop closed
            if np.linalg.norm(ring.root.start - ring.end) < APPROX_ZERO:
                ring.next = ring.root
                rings.append(ring.root)
                if not np.isinf(segments).all():
                    i, _, _ = np.where(~np.isinf(segments))
                    ring = Node(segments[i[0], 1, :].copy(), segments[i[0], 0, :].copy())
                    segments[i[0], :, :] = np.inf

        if miss and not np.isinf(segments).all():
            # bad ring
            i, _, _ = np.where(~np.isinf(segments))
            ring = Node(segments[i[0], 1, :].copy(), segments[i[0], 0, :].copy())
            segments[i[0], :, :] = np.inf

    polygons = []
    for ring in rings:
        ps = []
        current: Node = ring.next
        while current.root is not None:
            ps.append(current.start)
            current = current.next
        ps.append(current.start)
        if len(ps) < 3:
            continue
        polygons.append(orient(Polygon(shell=ps)))

    return polygons


def containsPoint2d(point, polygon: Polygon):
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
    polygon = polygonFromBody(point[2], body)
    return containsPoint2d(point[:2], polygon)
