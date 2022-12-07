from math import floor
from multiprocessing import Pool
from viewplanning.store import MongoCollectionStore
from .subapplication import Subapplication
from viewplanning.models import Experiment, RegionGroup, Solution
import logging
from .run import _run
import os
import json
from uuid import UUID


TEMP_DIR = 'data/tmp/'


def run(experiment):
    _run(experiment, dryRun=False)


class TestExperiments(Subapplication):
    def __init__(self):
        super().__init__('test')

    def run(self, args):

        if not os.path.exists(TEMP_DIR):
            os.mkdir(TEMP_DIR)

        logging.info('Loading Experiments')
        regionStore = MongoCollectionStore[RegionGroup]('regions', RegionGroup.from_dict)
        with open('./data/test/regions.json') as f:
            regionGroups = json.load(f)
            for group in regionGroups:
                group['_id'] = UUID(group['_id'])
                group = RegionGroup.from_dict(group)
                if not regionStore.hasId(group._id):
                    regionStore.insertItem(group)

        experimentStore = MongoCollectionStore[Experiment]('experiments', Experiment.from_dict)
        resultsStore = MongoCollectionStore[Solution]('results', Solution.from_dict)
        with open('./data/test/experiments.json') as f:
            experiments = json.load(f)
            for experiment in experiments:
                experiment['_id'] = UUID(experiment['_id'])
                experiment = Experiment.from_dict(experiment)
                if not experimentStore.hasId(experiment._id):
                    experimentStore.insertItem(experiment)
                if resultsStore.hasId(experiment._id):
                    resultsStore.collection.delete_one({'_id': experiment._id})

        logging.info("Starting Experiments")
        cpus = min(floor(os.cpu_count() * .7), os.cpu_count() - 1)  # don't take all cores
        with Pool(cpus) as pool:
            pool.map(run, [Experiment.from_dict(experiment) for experiment in experiments])
        logging.info('Finished all experiments')
