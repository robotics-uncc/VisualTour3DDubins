import logging
from .subapplication import Subapplication
from argparse import ArgumentParser, Namespace
from uuid import UUID
from viewplanning.plotting import SolutionPlotter3dPyvista, SolutionPlotter2dRegions
from viewplanning.store import MongoCollectionStore
from viewplanning.models import RegionGroup, Solution, VertexType
import os
import pyvista as pv
import numpy as np


class View(Subapplication):
    '''
    plots completed experiments
    '''

    def __init__(self):
        super().__init__('view')
        self.description = 'View the results of an experiment.'

    def modifyParser(self, parser: ArgumentParser):
        parser.add_argument('--regions', default=None, type=UUID, required=False, help='UUID of the group of visibility volumes')
        parser.add_argument('--solution', default=None, type=UUID, required=False, help='UUID of the solution to plot')
        parser.add_argument('--environment', default=None, type=str, required=False, help='environment map to plot *.obj')
        parser.add_argument('--out', default=None, type=str, required=False, help='file to save output to')
        return super().modifyParser(parser)

    def run(self, args: Namespace):
        if args.environment is None:
            environment = None
        else:
            reader = pv.get_reader(args.environment)
            environment: pv.PolyData = reader.read()
            environment = environment.transform(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]))

        if args.regions is not None and args.solution is None:
            self.plotRegions(environment, args.regions, args.out)
        elif args.solution is not None and args.regions is None:
            self.plotSolution(environment, args.solution, args.out)
        else:
            logging.log(logging.ERROR, 'Cannot pass agruments for --solution and --regions')

    def plotRegions(self, environment: pv.PolyData, id: UUID, outFile: str):

        plotter = SolutionPlotter3dPyvista(environment)

        regionStore = MongoCollectionStore[RegionGroup]('regions', RegionGroup.from_dict)
        regions = regionStore.getItemById(id)
        if regions is None:
            logging.log(logging.ERROR, f'Could not find regions with id {id}')
            return

        plotter.plot(regions.regions, [])

        if outFile is None:
            return

        plotter.savePlot(outFile)

    def plotSolution(self, environment: pv.PolyData, id: UUID, outFile: str):

        resultStore = MongoCollectionStore[Solution]('results', Solution.from_dict)
        results = resultStore.getItemById(id)
        if results is None:
            logging.log(logging.ERROR, f'Could not find solution with id {id}')
            return

        if results.samples[0].type == VertexType.TWO_D:
            plotter = SolutionPlotter2dRegions()
        else:
            plotter = SolutionPlotter3dPyvista(environment)

        plotter.plot(results.experiment.regions, results.edges)

        if outFile is None:
            return

        plotter.savePlot(outFile)
