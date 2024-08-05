from viewplanning.cli.subapplication import Subapplication
from argparse import ArgumentParser
from viewplanning.store import CollectionStoreFactory
from viewplanning.models import RegionGroup, Region
import logging
import os
import subprocess
import pyvista as pv
from viewplanning.cli.create.viewVolumes import modifyMesh
import tqdm


class FixViewVolumes(Subapplication):
    '''
    fixes broken view volumes
    '''

    def __init__(self):
        super().__init__('fixviewvolumes')
        self.description = 'Repair view volumes broken in creation process.'

    def modifyParser(self, parser: ArgumentParser):
        parser.add_argument('--group', dest='group', required=True, type=str, help='group of volumes to check')
        parser.add_argument('--map', dest='map', required=True, type=str, help='environment map for the view volumes *.obj')
        parser.add_argument('--radius', dest='radius', default=300, type=float, help='sensing distance limist for the aircraft')
        parser.add_argument('--decimate', dest='decimate', default=500, type=int, help='numer of faces for the resulting mesh')
        parser.add_argument('--cone', dest='cone', type=bool, default=False, help='use a body fixed camera')
        parser.add_argument('--fov', type=float, dest='fov', default=24.4, help='FOV of the body fixed camera')
        super().modifyParser(parser)

    def run(self, args):
        storeFactory = CollectionStoreFactory()
        store = storeFactory.getStore('regions', RegionGroup.from_dict)
        groups = [group for group in store.getItems() if group.group == args.group]
        outfile = 'fix.yaml'

        with open('data/template/worldTemplate.txt') as f:
            worldTemplate = f.read()
        with open('data/template/volumeTemplate.txt') as f:
            volumeTemplate = f.read()
        with open(outfile, 'w') as f:
            f.write(worldTemplate.format('world', os.path.abspath(args.map)))
            i = 0
            regions: list[Region] = []
            for group in groups:
                for region in group.regions:
                    if not (region.file.endswith('.obj') or not os.path.exists(region.file)):
                        continue
                    out = region.file if region.file.endswith('.obj') else region.file.replace('.ply', '.obj')

                    regions.append(region)
                    logging.info(f'fixing object {region}')
                    f.write(volumeTemplate.format(i, region.points[0][0], -region.points[0][1], region.points[0][2], args.radius, os.path.abspath(out)))
                    i += 1
                    region.file = out
        subprocess.run(['./ogl_depthrenderer', '-c', os.path.abspath(outfile)], cwd='subs/OpenGLDepthRenderer/build/bin/', stdout=subprocess.DEVNULL)

        for region in tqdm.tqdm(regions):
            modifyMesh(region, args.decimate, args.cone, args.radius, args.fov, region.points[0])

        for group in groups:
            store.updateItem(group)
        store.close()
