from math import floor
from multiprocessing import Pool, TimeoutError
from multiprocessing.dummy import Pool as ThreadPool
from viewplanning.store import MongoCollectionStore
from viewplanning.models import Experiment, Solution
from viewplanning.solvers import makeSolver, DubinsSolver
from viewplanning.sampling import SamplingFailedException
from viewplanning.configuration import ConfigurationFactory
import logging
import time
import os
from .subapplication import Subapplication
from argparse import ArgumentParser
from uuid import UUID
from pymongo import ASCENDING


TEMP_DIR = 'data/tmp/'


def _run(experiment: Experiment, dryRun=False):
    resultsStore = MongoCollectionStore[Solution]('results', Solution)
    solver = makeSolver(experiment)
    try:
        logging.info(f'starting {experiment._id}')
        start = time.time()
        edges = solver.solve()
        delta = time.time() - start
        cost = sum([edge.cost for edge in edges])
        verified = solver.verify()
        solution = Solution(cost, delta, edges, experiment, True, experiment._id, solver.vertices, verified)
        if not dryRun:
            resultsStore.insertItem(solution)
        logging.info(f'finished {solution._id} cost {cost} time {delta}')
    except SamplingFailedException as e:
        logging.warn(f'experiment {experiment._id} failed {e.args[0]}')
    except Exception as e:
        logging.exception(f'error solving {experiment._id}')
        return


class RunExperiments(Subapplication):
    '''
    Runs experiments stored in database
    '''

    def __init__(self):
        super().__init__('run')
        self.description = 'Run all non-completed experiments stored in database or a single non-completed experiment by id.'

    def modifyParser(self, parser: ArgumentParser):
        parser.add_argument('--id', default=None, type=UUID, required=False, help='UUID of the experiment to run')
        return super().modifyParser(parser)

    def run(self, args):

        if not os.path.exists(TEMP_DIR):
            os.mkdir(TEMP_DIR)

        experimentStore = MongoCollectionStore[Experiment]('experiments', Experiment.from_dict)
        # single experiment
        if args.id is not None:
            experiment = experimentStore.getItemById(args.id)
            if experiment is None:
                return
            _run(experiment, dryRun=True)
            return

        experiments = experimentStore.getItemsIterator(sort=[
            ('sampleStrategy.numPhi', ASCENDING),
            ('sampleStrategy.numTheta', ASCENDING),
            ('sampleStrategy.numSamples', ASCENDING),
        ])
        resultsStore = MongoCollectionStore[Solution]('results', Solution)
        toExecute = []
        for experiment in experiments:
            if not resultsStore.getItemById(experiment._id):
                toExecute.append(experiment)

        logging.info("Starting Experiments")
        cpus = min(floor(os.cpu_count() * .7), os.cpu_count() - 1)  # don't take all cores
        with Pool(cpus) as pool:
            pool.map(_run, toExecute)
        logging.info('Finished all experiments')
