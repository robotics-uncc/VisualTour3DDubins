from argparse import ArgumentParser
import subprocess
import numpy as np
from shapely.geometry import Polygon, Point
import os
from viewplanning.models import Region, RegionType, RegionGroup
from viewplanning.store import CollectionStoreFactory, readObj
from viewplanning.cli.subapplication import Subapplication
from viewplanning.sampling import polygonsFromMesh, containsPoint2d
import logging
import pyvista as pv
import tqdm


class MaxIterationException(Exception):
    pass


APPROX_ZERO = .0001
MAX_ITERATIONS = 1000
MAX_ATTEMPTS = 10


class ViewVolumes(Subapplication):
    def __init__(self):
        super().__init__('viewvolumes')

    def modifyParser(self, parser: ArgumentParser):
        parser.add_argument('--gridPoints', dest='gridPoints', default=256, type=int, help='number of grid point to test for height of environment')
        parser.add_argument('--worldMap', dest='worldMap', default='data/worldMaps/uptownCharlotte.obj', type=str, help='world map to use *.obj')
        parser.add_argument('--maxDistance', dest='maxDistance', default=600, type=float, help='min distance between targets')
        parser.add_argument('--group', dest='group', default='vv', type=str, help='name of group')
        parser.add_argument('--radius', dest='radius', type=float, default=300, help='max viewing distance')
        parser.add_argument('--out', dest='out', type=str, default='data/viewRegions/', help='output dir for volumes')
        parser.add_argument('--minHeight', dest='minHeight', type=float, default=150, help='min altitude')
        parser.add_argument('--delta', dest='delta', type=float, default=150, help='min height to view target')
        parser.add_argument('--numGroups', dest='numGroups', type=int, default=20, help='number of sets of visbility volumes to create')
        parser.add_argument('--targets', dest='targets', type=int, nargs=3, default=[2, 2, 1], help='points on ground plane, roofs and walls')
        parser.add_argument('--areapct', dest='areapct', type=float, default=1.0, help='percentage of map area to use')
        parser.add_argument('--close', dest='close', type=bool, default=False, help='allow visibility volumes to be within max distance')
        parser.add_argument('--decimate', dest='decimate', type=int, default=500, help='number of faces for the resulting meshes')
        parser.add_argument('--cone', dest='cone', type=bool, default=False, help='use body fixed camera model')
        parser.add_argument('--fov', type=float, dest='fov', default=24.4, help='FOV of the body fixed camera model')
        parser.add_argument('--groupStart', type=int, dest='groupStart', default=0, help='start at index partway through')
        super().modifyParser(parser)

    def run(self, args):
        logging.info("Reading in World Map")
        map = readObj(args.worldMap, rotationMatrix=np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]]))
        logging.info("Iterating through all the faces")
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
        for i in tqdm.tqdm(range(map.n_faces)):
            face = map.faces.reshape([-1, 4])[i, 1:]
            vertices = map.points[face]
            if sum((vertices[:, 0] > xEnd) | (vertices[:, 1] > yEnd)) > 0:
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
        for g in range(args.groupStart, args.groupStart + args.numGroups):
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
                        point = buildingSides[index[0]][0, :] * (1 - r1) + buildingSides[index[0]][1, :] * r1 * \
                            (1 - r2) + buildingSides[index[0]][2, :] * r1 * r2 + .5 * n
                        if not outsideAllBuildings(map, point):
                            point = buildingSides[index[0]][0, :] * (1 - r1) + buildingSides[index[0]][1, :] * r1 * \
                                (1 - r2) + buildingSides[index[0]][2, :] * r1 * r2 - .5 * n
                            if not outsideAllBuildings(map, point):
                                continue
                        if not args.close and closeToOthers(point, points, args.maxDistance):
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
                        n = np.array([0, 0, 1])
                        # find random point and move slightly off face
                        point = buildingTops[index[0]][0, :] * (1 - r1) + buildingTops[index[0]][1, :] * r1 * \
                            (1 - r2) + buildingTops[index[0]][2, :] * r1 * r2 + .5 * n
                        if not args.close and closeToOthers(point, points, args.maxDistance):
                            continue
                        if point[0, 2] > args.radius - args.maxDistance:
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
                        if not outsideAllBuildings(map, point):
                            continue
                        if z < APPROX_ZERO and not args.close and closeToOthers(point, points, args.maxDistance) and not outsideAllBuildings(map, point):
                            continue
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
                            f.write(volumeTemplate.format(i, point[0], -point[1], point[2], args.radius, os.path.abspath(fname)))
                            regions.append(Region(type=RegionType.WAVEFRONT, file=fname, rotationMatrix=np.array(
                                [[1, 0, 0], [0, 0, -1], [0, 1, 0]]), points=[point]))
                            i += 1

                    subprocess.run(['./ogl_depthrenderer', '-c', os.path.abspath(outfile)],
                                   cwd='subs/OpenGLDepthRenderer/build/bin/', stdout=subprocess.DEVNULL)
                    os.remove(outfile)
                    for region in regions:
                        z = max(region.points[0][2] + args.delta, args.minHeight)
                        region.z = z
                        modifyMesh(region, args.decimate, args.cone, args.radius, args.fov, region.points[0])
                    regionGroups.append(RegionGroup(regions=regions, group=args.group))
                    break
                except MaxIterationException as e:
                    continue
                finally:
                    w += 1
        storeFactory = CollectionStoreFactory()
        store = storeFactory.getStore('regions', RegionGroup.from_dict)
        for item in regionGroups:
            store.insertItem(item)
        store.close()
        return len(regionGroups)


def closeToOthers(point, points, maxDistance):
    for p in points:
        if np.linalg.norm(point - p) < maxDistance:
            return True
    return False


def outsideAllBuildings(env: pv.PolyData, point: np.ndarray):
    p = point.reshape([3])
    polygons = polygonsFromMesh(p[2], env)
    for polygon in polygons:
        if containsPoint2d(p, polygon):
            return False
    return True


def normal(vertices):
    # get normal
    a = vertices[0, :]
    b = vertices[1, :]
    c = vertices[2, :]
    ba = b - a
    ac = c - a
    n = np.cross(ba, ac)
    return n / np.linalg.norm(n)


def modifyMesh(region: Region, vertices, useCone, radius, fov, point):
    if not os.path.exists(region.file):
        return
    if region.file.endswith('.obj'):
        out = region.file.replace('.obj', '.ply')
    args = [
        'blender', '-b', '--python', 'viewplanning/cli/create/helper/modifyViewRegions.py',
        '--', region.file,
        '--out', out,
        '--height', str(region.z),
        '--decimate', str(vertices),
        '--radius', str(radius),
        '--point', str(point[0]), str(point[1]), str(point[2]),
        '--fov', str(fov)
    ]
    if useCone:
        args += ['--cone', str(useCone)]
    subprocess.run(args, stdout=subprocess.DEVNULL)
    if os.path.exists(out):
        region.rotationMatrix = np.eye(3).tolist()
        os.remove(region.file)
        region.file = out
    else:
        logging.warn(f'Couldn\'t modify mesh {region.file}')
