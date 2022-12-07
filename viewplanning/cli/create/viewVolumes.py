from argparse import ArgumentParser
import subprocess
import numpy as np
from shapely.geometry import Polygon, Point
import os
from viewplanning.models import Region, RegionType, RegionGroup
from viewplanning.store import MongoCollectionStore, readObj
from viewplanning.cli.subapplication import Subapplication
import logging
import pyvista as pv


class MaxIterationException(Exception):
    pass


APPROX_ZERO = .0001
MAX_ITERATIONS = 1000
MAX_ATTEMPTS = 10
RESULTING_FACES = 500


class ViewVolumes(Subapplication):
    def __init__(self):
        super().__init__('viewvolumes')

    def modifyParser(self, parser: ArgumentParser):
        parser.add_argument('--gridPoints', dest='gridPoints', default=256, type=int)
        parser.add_argument('--worldMap', dest='worldMap', default='data/worldMaps/uptownCharlotte.obj', type=str)
        parser.add_argument('--maxDistance', dest='maxDistance', default=600, type=float)
        parser.add_argument('--group', dest='group', default='vv', type=str)
        parser.add_argument('--radius', dest='radius', type=float, default=300)
        parser.add_argument('--out', dest='out', type=str, default='data/tmp/')
        parser.add_argument('--minHeight', dest='minHeight', type=float, default=150)
        parser.add_argument('--delta', dest='delta', type=float, default=150)
        parser.add_argument('--numGroups', dest='numGroups', type=int, default=20)
        parser.add_argument('--targets', dest='targets', type=int, nargs=3, default=[2, 2, 1])
        parser.add_argument('--areapct', dest='areapct', type=float, default=1.0)
        super().modifyParser(parser)

    def run(self, args):
        map = readObj(args.worldMap, rotationMatrix=np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]]))
        xStart, xEnd, yStart, yEnd, _, _ = map.bounds
        xEnd = xStart + (xEnd - xStart) * np.sqrt(args.areapct)
        yEnd = yStart + (yEnd - yStart) * np.sqrt(args.areapct)

        gridPoints = args.gridPoints
        uX = (xEnd - xStart) / gridPoints
        uY = (yEnd - yStart) / gridPoints

        zHeights = np.zeros([gridPoints, gridPoints])
        buildingSides = []
        sideProbability = []
        buildingTops = []
        topProbability = []
        # sort into ground plane, building roof, building wall faces
        k = np.array([0, 0, 1])
        for i in range(map.n_cells):
            vertices = map.cell_points(i)
            inBounds = False
            for j in range(vertices.shape[1]):
                if vertices[0, j] < xEnd or vertices[1, j] < yEnd:
                    inBounds = True
                    break
            if not inBounds:
                continue
            a = vertices[0, :]
            b = vertices[1, :]
            c = vertices[2, :]
            n = normal(vertices)
            # face parallel to ground plane
            if np.abs(np.dot(n, k)) > APPROX_ZERO:
                z = (a[2] + b[2] + c[2]) / 3
                if z < APPROX_ZERO:
                    continue
                buildingTops.append(vertices)
                topProbability.append(.5 * np.linalg.norm(np.cross(vertices[0, :] - vertices[1, :], vertices[0, :] - vertices[2, :])))

                polygon = Polygon(shell=vertices[:, :2])
                iStart = int(np.floor((vertices[:, 0].min() - xStart) / uX))
                iEnd = int(np.floor((vertices[:, 0].max() - xStart) / uX))
                jStart = int(np.floor((vertices[:, 1].min() - yStart) / uY))
                jEnd = int(np.floor((vertices[:, 1].max() - yStart) / uY))
                for i in range(iStart, iEnd + 1):
                    for j in range(jStart, jEnd + 1):
                        p = Point(xStart + uX * i + uX / 2, yStart + uY * j + uY / 2)
                        if polygon.contains(p) and i < gridPoints and j < gridPoints:
                            zHeights[i, j] = z
            else:
                buildingSides.append(vertices)
                sideProbability.append(.5 * np.linalg.norm(np.cross(vertices[0, :] - vertices[1, :], vertices[0, :] - vertices[2, :])))

        totalArea = sum(sideProbability)
        for i in range(len(sideProbability)):
            sideProbability[i] /= totalArea
        totalArea = sum(topProbability)
        for i in range(len(topProbability)):
            topProbability[i] /= totalArea

        regionGroups = []
        for g in range(args.numGroups):
            logging.info(f'starting group {g}')
            w = 0
            while w < MAX_ATTEMPTS:
                try:
                    t = args.targets
                    numSidePoints = t[0]
                    numTopPoints = t[1]
                    numFloorPoints = t[2]
                    sidePoints = 0
                    points = []
                    i = 0
                    while i < MAX_ITERATIONS and sidePoints < numSidePoints:
                        i += 1
                        index = np.random.choice(range(len(buildingSides)), 1, p=sideProbability)
                        r1 = np.sqrt(np.random.random(size=[1, 1]))
                        r2 = np.random.random(size=[1, 1])
                        n = normal(buildingSides[index[0]])
                        # find random point and move slightly off face
                        point = buildingSides[index[0]][0, :] * (1 - r1) + buildingSides[index[0]][1, :] * r1 * (1 - r2) + buildingSides[index[0]][2, :] * r1 * r2 + .5 * n
                        if closeToOthers(point, points, args.maxDistance):
                            continue
                        points.append(point[0].tolist())
                        sidePoints += 1
                    if i >= MAX_ITERATIONS:
                        raise MaxIterationException('Cannot find appropriately spaced points')

                    i = 0
                    topPoints = 0
                    while i < MAX_ITERATIONS and topPoints < numTopPoints:
                        i += 1
                        index = np.random.choice(range(len(buildingTops)), 1, p=topProbability)
                        r1 = np.sqrt(np.random.random(size=[1, 1]))
                        r2 = np.random.random(size=[1, 1])
                        n = normal(buildingTops[index[0]])
                        # find random point and move slightly off face
                        point = buildingTops[index[0]][0, :] * (1 - r1) + buildingTops[index[0]][1, :] * r1 * (1 - r2) + buildingTops[index[0]][2, :] * r1 * r2 + .5 * n
                        if closeToOthers(point, points, args.maxDistance):
                            continue
                        points.append(point[0].tolist())
                        topPoints += 1
                    if i >= MAX_ITERATIONS:
                        raise MaxIterationException('Cannot find appropriately spaced points')

                    i = 0
                    floorPoints = 0
                    while i < MAX_ITERATIONS and floorPoints < numFloorPoints:
                        i += 1
                        xy = np.random.randint(0, gridPoints, [2])
                        z = np.abs(zHeights[xy[0], xy[1]])
                        point = np.array([xStart + uX * xy[0] + uX / 2, yStart + uY * xy[1] + uY / 2, z + .5])
                        if closeToOthers(point, points, args.maxDistance):
                            continue
                        if z < APPROX_ZERO:
                            points.append(point.tolist())
                            floorPoints += 1

                    if i >= MAX_ITERATIONS:
                        raise MaxIterationException('Cannot find appropriately spaced points')

                    # run view volume generation program
                    if not os.path.exists(args.out):
                        os.mkdir(args.out)
                    with open('data/template/worldTemplate.txt') as f:
                        worldTemplate = f.read()
                    with open('data/template/volumeTemplate.txt') as f:
                        volumeTemplate = f.read()

                    outfile = args.out + f'out_{os.getpid()}.yaml'
                    regions: 'list[Region]' = []
                    with open(outfile, 'w') as f:
                        f.write(worldTemplate.format('world', os.path.abspath(args.worldMap)))
                        i = 0
                        for point in points:
                            fname = f'{args.out}{args.group}_g_{g:03d}_t_{sum(t):03d}_v_{i:03d}.obj'
                            f.write(volumeTemplate.format(i, point[0], point[1], point[2], args.radius, os.path.abspath(fname)))
                            regions.append(Region(type=RegionType.WAVEFRONT, file=fname, rotationMatrix=np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]]), points=[point]))
                            i += 1

                    subprocess.run(['./ogl_depthrenderer', '-c', os.path.abspath(outfile)], cwd='subs/OpenGLDepthRenderer/build/bin/', stdout=subprocess.DEVNULL)
                    os.remove(outfile)
                    for region in regions:
                        z = max(region.points[0][2] + args.delta, args.minHeight)
                        region.z = z
                        modifyMesh(region)
                    regionGroups.append(RegionGroup(regions=regions, group=args.group))
                    break
                except MaxIterationException as e:
                    continue
                finally:
                    w += 1
        store = MongoCollectionStore[RegionGroup]('regions', RegionGroup.from_dict)
        for item in regionGroups:
            store.insertItem(item)
        return len(regionGroups)


def closeToOthers(point, points, maxDistance):
    for p in points:
        if np.linalg.norm(point - p) < maxDistance:
            return True
    return False


def normal(vertices):
    # get normal
    a = vertices[0, :]
    b = vertices[1, :]
    c = vertices[2, :]
    ba = b - a
    ac = a - c
    n = np.cross(ba, ac)
    return n / np.linalg.norm(n)


def modifyMesh(region: Region):
    if not os.path.exists(region.file):
        return

    reader = pv.get_reader(region.file)
    vv: pv.PolyData = reader.read()
    transform = np.eye(4)
    transform[:3, :3] = region.rotationMatrix
    vv.transform(transform)
    vv = vv.decimate(.99)

    x0, x1, y0, y1, z0, z1 = vv.bounds
    cube = pv.Cube(bounds=(x0 - 10, x1 + 10, y0 - 10, y1 + 10, -10, region.z))
    cube.triangulate(inplace=True)
    newVV = vv.boolean_difference(cube)
    if newVV.n_cells == 0:
        logging.warning(f'view volume {region.file} invalid!')
    d = 1 - RESULTING_FACES / newVV.n_faces
    if d > 0:
        newVV = newVV.decimate(d)

    newVV.save(region.file)
