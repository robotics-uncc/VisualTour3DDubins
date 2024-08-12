from multiprocessing import Queue, Process
from viewplanning.store import CollectionStoreFactory
from .subapplication import Subapplication
from viewplanning.models import Experiment, RegionGroup, Solution
from viewplanning.configuration import ConfigurationFactory
import logging
from .run import _run
import time
import json
from uuid import UUID
from math import floor
import os


TEMP_DIR = 'data/tmp/'


def run(experiment, writeQueue):
    '''
    run an experiment and place the result on the writeQueue

    Parameters
    ----------
    experiment: Experiment
        expreiment to run
    writeQueue: Queue
        queue to place the experiemntal result on
    '''
    _run(Experiment.from_dict(experiment), writeQueue, dryRun=False)
    return 0


class TestExperiments(Subapplication):
    '''
    Inserts text experiments into database and runs them
    '''

    def __init__(self):
        super().__init__('test')
        self.description = 'Load a small set of experiments into the database and execute them.'

    def run(self, args):
        config = ConfigurationFactory.getInstance()
        storeFactory = CollectionStoreFactory()

        if not os.path.exists(TEMP_DIR):
            os.mkdir(TEMP_DIR)
        logging.info('Loading Experiments')
        regionStore = storeFactory.getStore('regions', RegionGroup.from_dict)
        with open('./data/test/regions.json') as f:
            regionGroups = json.load(f)
            for group in regionGroups:
                group['_id'] = UUID(group['_id'])
                group = RegionGroup.from_dict(group)
                if not regionStore.hasId(group._id):
                    regionStore.insertItem(group)
        regionStore.close()

        experimentStore = storeFactory.getStore(
            'experiments', Experiment.from_dict)
        with open('./data/test/experiments.json') as f:
            experiments = json.load(f)
            for experiment in experiments:
                experiment['_id'] = UUID(experiment['_id'])
                experiment = Experiment.from_dict(experiment)
                if experimentStore.hasId(experiment._id):
                    experimentStore.removeItem(experiment._id)
                experimentStore.insertItem(experiment)
        experimentStore.close()
        resultStore = storeFactory.getStore('results', Solution.from_dict)
        for experiment in experiments:
            resultStore.removeItem(experiment['_id'])

        writeQueue = Queue()

        logging.info("Starting Experiments")
        if config['process']['multithreading']:
            cpus = min(floor(os.cpu_count() * .7), os.cpu_count() -
                       1, len(experiments))  # don't take all cores
            processes = [
                Process(target=run, args=[experiments.pop(), writeQueue]) for i in range(cpus)]
            for process in processes:
                process.start()
            while len(experiments) > 0:
                for i in range(len(processes)):
                    if not processes[i].is_alive():
                        processes[i].close()
                        t = processes[i]
                        if len(experiments) > 0:
                            processes[i] = Process(
                                target=run, args=[experiments.pop(), writeQueue])
                            processes[i].start()
                        del t
                        while not writeQueue.empty():
                            resultStore.insertItem(writeQueue.get())
                time.sleep(1.0)

            def anyAlive(processes: 'list[Process]'):
                count = 0
                for process in processes:
                    try:
                        count += 1 if process.is_alive() else 0
                    except:
                        pass
                return count > 0

            while anyAlive(processes):
                while not writeQueue.empty():
                    resultStore.insertItem(writeQueue.get())
                time.sleep(1.0)
        else:
            for exp in experiments:
                run(exp, writeQueue)

        while not writeQueue.empty():
            resultStore.insertItem(writeQueue.get())
        resultStore.close()

        logging.info('Finished all experiments')
