from viewplanning.cli.subapplication import Subapplication
from argparse import ArgumentParser
from viewplanning.store import MongoCollectionStore
from viewplanning.models import RegionGroup, Region
import logging
import os
import subprocess
from viewplanning.cli.create.viewVolumes import modifyMesh


class FixViewVolumes(Subapplication):
    def __init__(self):
        super().__init__('fixviewvolumes')
        self.description = 'Repair view volumes broken in creation process.'

    def modifyParser(self, parser: ArgumentParser):
        parser.add_argument('--size', dest='size', default=80, type=float, help='size of file in kB as broken mesh cutoff')
        parser.add_argument('--radius', dest='radius', default=300, type=float, help='sensing distance limist for the aircraft')
        parser.add_argument('--map', dest='map', default='./worldMaps/uptownCharlotte.obj', type=str, help='environment map for the view volumes *.obj')
        super().modifyParser(parser)

    def run(self, args):
        store = MongoCollectionStore[RegionGroup]('regions', RegionGroup.from_dict)
        groups = store.getItems()

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
                    if not os.path.exists(region.file):
                        continue

                    size = os.path.getsize(region.file)
                    if size > args.size * 2 ** 10 and size < 2 ** 20:
                        continue
                    regions.append(region)
                    logging.info(f'fixing object {region}')
                    f.write(volumeTemplate.format(i, region.points[0][0], region.points[0][1], region.points[0][2], args.radius, os.path.abspath(region.file)))
                    i += 1

        subprocess.run(['./ogl_depthrenderer', '-c', os.path.abspath(outfile)], cwd='subs/OpenGLDepthRenderer/build/bin/', stdout=subprocess.DEVNULL)

        for region in regions:
            modifyMesh(region)
