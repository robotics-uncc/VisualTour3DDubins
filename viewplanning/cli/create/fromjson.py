from argparse import ArgumentParser, FileType
import subprocess
import numpy as np
import os
from viewplanning.models import Region, RegionType, RegionGroup
from viewplanning.store import CollectionStoreFactory, readObj
from viewplanning.cli.subapplication import Subapplication
import logging
import json
from dataclasses import asdict


class MaxIterationException(Exception):
    pass


APPROX_ZERO = .0001
MAX_ITERATIONS = 1000
MAX_ATTEMPTS = 10


class FromJson(Subapplication):
    '''
    create a set of view volumes for a json file

    example file
    
    {
        "group": "experimental",
        "out": "data/viewRegions/",
        "worldMap": "data/worldMaps/uptownCharlotte.obj",
        "rotation": [
            [
                1,
                0,
                0
            ],
            [
                0,
                0,
                -1
            ],
            [
                0,
                1,
                0
            ]
        ],
        "targets": [
            [
                107.85001846705563,
                96.57923833141103,
                -6.63042
            ],
            [
                -19.870211353118066,
                67.76666204212233,
                4.20898
            ]
        ],
        "delta": 28.9,
        "minHeight": 37.5,
        "radius": 72.2,
        "decimate": 500,
        "cone": true,
        "fov": 23.5,
        "lat": 35.22642325614007,
        "lon": -80.8398158161177,
        "alt": 223.5
        35.22642325614007, -80.8398158161177
    }
    '''
    def __init__(self):
        super().__init__('fromjson')

    def modifyParser(self, parser: ArgumentParser):
        parser.add_argument('--json', dest='json', type=FileType('r'), required=True)
        super().modifyParser(parser)

    def run(self, args):
        try:
            config = json.load(args.json)
            group = config.get('group', 'experimental')
            out = config.get('out', 'data/tmp')
            worldMap = config.get('worldMap', 'data/worldMaps/uptownCharlotte.obj')
            rotation = config.get('rotation', np.eye(3))
            points = config.get('targets', [[0, 0]])
            delta = config.get('delta', 75)
            minHeight = config.get('minHeight', 75)
            radius = config.get('radius', 300)
            decimate = config.get('decimate', 500)
            cone = config.get('cone', False)
            fov = config.get('fov', 24.4)

            env = readObj(worldMap, rotation)

            logging.info(f'starting group {group}')

            # run view volume generation program
            if not os.path.exists(out):
                os.mkdir(out)
            with open('data/template/worldTemplate.txt') as f:
                worldTemplate = f.read()
            with open('data/template/volumeTemplate.txt') as f:
                volumeTemplate = f.read()

            outfile = out + f'out_{os.getpid()}.yaml'
            regions: 'list[Region]' = []
            with open(outfile, 'w') as f:
                f.write(worldTemplate.format('world', os.path.abspath(worldMap)))
                for i, point in enumerate(points):
                    fname = f'{out}{group}_v_{i:03d}.obj'
                    f.write(volumeTemplate.format(i, point[0], -point[1], point[2], radius, os.path.abspath(fname)))
                    regions.append(Region(type=RegionType.WAVEFRONT, file=fname, rotationMatrix=rotation, points=[point]))

            result = subprocess.run(['./ogl_depthrenderer', '-c', os.path.abspath(outfile)],
                                    cwd=os.path.abspath('subs/OpenGLDepthRenderer/build/bin/'), capture_output=True)
            for region in regions:
                z = max(region.points[0][2] + delta, minHeight)
                region.z = z
                modifyMesh(region, decimate, cone, radius, fov, [region.points[0][0], -region.points[0][1], region.points[0][2]])
            regionGroup = RegionGroup(regions=regions, group=group)
            storeFactory = CollectionStoreFactory()
            store = storeFactory.getStore('regions', RegionGroup.from_dict)
            store.insertItem(regionGroup)
            store.close()
            return 1
        finally:
            if os.path.exists(outfile):
                os.remove(outfile)


def modifyMesh(region: Region, vertices, useCone, radius, fov, point):
    if not os.path.exists(region.file):
        return
    out = region.file.replace('.obj', '.ply')
    logging.info(f'loading blender for modifying {region.file}')
    subprocess.run([
        'blender', '-b', '--python', 'viewplanning/cli/create/helper/modifyViewRegions.py',
        '--', region.file,
        '--out', out,
        '--height', str(region.z),
        '--decimate', str(vertices),
        '--cone', str(useCone),
        '--radius', str(radius),
        '--point', str(point[0]), str(-point[1]), str(point[2]),
        '--fov', str(fov)
    ], stdout=subprocess.DEVNULL)
    if os.path.exists(out):
        region.rotationMatrix = np.eye(3).tolist()
        os.remove(region.file)
        region.file = out
    else:
        logging.warn(f'Couldn\'t modify mesh {region.file}')
