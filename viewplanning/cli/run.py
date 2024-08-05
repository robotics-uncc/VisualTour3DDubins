from multiprocessing import Process, TimeoutError, Queue
from viewplanning.store import CollectionStoreFactory
from viewplanning.models import Experiment, Solution
from viewplanning.solvers import makeSolver, DubinsSolver
from viewplanning.sampling import SamplingFailedException
from viewplanning.configuration import ConfigurationFactory
import logging
import time
import os
from .subapplication import Subapplication
from viewplanning.configuration import ConfigurationFactory
from argparse import ArgumentParser, FileType
from uuid import UUID
from pymongo import ASCENDING
import pandas as pd
import shutil
from math import floor
import psutil
import signal


TIMEOUT = 3 * 60 * 60
MEMORY_KILL = 80
KILL_PROCESS = 5
TEMP_DIR = 'data/tmp/'


def _run(experiment: Experiment, writeQueue: Queue, dryRun=False):
    '''
    run an experiment and place the result on the queue. Don't place the result of the queue if dry run is True

    Parameters
    ----------
    experiment: Experiment
        experiment to run
    writeQueue: Queue
        queue to place the result of the experiment on
    dryTrue:
        do place the result on the queue if True
    
    Returns
    -------
        int
    '''
    solver = makeSolver(experiment)
    try:
        logging.info(f'starting {experiment._id} pid {os.getpid()}')
        start = time.time()
        edges = solver.solve()
        delta = time.time() - start
        cost = sum([edge.cost for edge in edges])
        verified = solver.verify()
        solution = Solution(cost, delta, edges, experiment, True, experiment._id, solver.vertices, verified)
        logging.info(f'finished {solution._id} cost {cost} time {delta}')
        if not dryRun:
            writeQueue.put(solution)
    except SamplingFailedException as e:
        logging.warning(f'sampling failed for experiment {experiment._id}, message {e.args[0]}', exc_info=True)
    except Exception as e:
        logging.exception(f'error solving {experiment._id}')
    finally:
        return 0


class RunExperiments(Subapplication):
    '''
    Runs experiments stored in database
    '''

    def __init__(self):
        super().__init__('run')
        self.description = 'Run all non-completed experiments stored in database or a single non-completed experiment by id.'

    def modifyParser(self, parser: ArgumentParser):
        parser.add_argument('--id', default=None, type=UUID, required=False, help='UUID of the experiment to run')
        parser.add_argument('--black', required=False, type=str, help='black list of experiment by UUID to not run')
        parser.add_argument('--group', default=None, required=False, type=str, help='group of experiments to run')
        return super().modifyParser(parser)

    def run(self, args):
        config = ConfigurationFactory.getInstance()
        storeFactory = CollectionStoreFactory()
        
        logging.info('deleting tmp dir')
        if os.path.exists('data/tmp'):
            shutil.rmtree('data/tmp')
        if os.path.exists('subs/GLKH/TMP'):
            shutil.rmtree('subs/GLKH/TMP')
        os.mkdir('subs/GLKH/TMP')
        os.mkdir('data/tmp')
        experimentStore = storeFactory.getStore('experiments', Experiment.from_dict)
        writeQueue = Queue()
        # single experiment
        if args.id is not None:
            experiment = experimentStore.getItemById(args.id)
            if experiment is None:
                return
            _run(experiment, writeQueue, dryRun=True)
            return

        if args.black is not None:
            blacklist = pd.read_csv(args.black)
            blacklist['id'] = blacklist['id'].apply(UUID)
        else:
            blacklist = pd.DataFrame(columns=['id'])

        experiments = experimentStore.getItemsIterator(sort=[
            ('sampleStrategy.numSamples', ASCENDING),
            ('sampleStrategy.numPhi', ASCENDING),
            ('sampleStrategy.numTheta', ASCENDING),
        ],
        search={
            'group': args.group
        })
        processes = []
        try:
            resultsStore = storeFactory.getStore('results', Solution)
            toExecute = []
            for experiment in experiments:
                if resultsStore.getItemById(experiment._id):
                    continue
                elif experiment._id in blacklist['id'].values:
                    continue
                toExecute.append(experiment)
            experimentStore.close()

            writeQueue = Queue()

            logging.info(f"Starting Experiments. Running {len(toExecute)} experiments.")
            if config['process']['multithreading']:
                cpus = min(floor(os.cpu_count() * .5), os.cpu_count() - 1, len(toExecute))  # don't take all cores
                processes = []
                for i in range(cpus):
                    experiment = toExecute.pop(0)
                    processes.append(
                        Process(
                            target=_run,
                            args=[experiment, writeQueue],
                            name=f'expr_{experiment._id}'
                        )
                    )
                for process in processes:
                    process.start()
                k = 0
                while len(toExecute) > 0:
                    for i in range(len(processes)):
                        # check is process is finished
                        if not processes[i].is_alive():
                            logging.info(f'process {processes[i].name} finished')
                            processes[i].close()
                            t = processes[i]
                            if len(toExecute) > 0:
                                experiment = toExecute.pop(0)
                                processes[i] = Process(target=_run, args=[experiment, writeQueue], name=f'expr_{experiment._id}')
                                processes[i].start()
                            del t
                    
                    # cacluate all memory useage and kill highest if usage is too high
                    memoryUsage = []
                    for i in range(len(processes)):
                        try:
                            oProcess = psutil.Process(processes[i].pid)
                            total = oProcess.memory_percent() + sum([child.memory_percent() for child in oProcess.children(recursive=True)])
                            memoryUsage.append((processes[i].pid, total))
                        except psutil.NoSuchProcess:
                            pass
                        except ValueError:
                            logging.exception('checkout process failed')
                    
                    i = 0
                    while i < len(memoryUsage):
                        if memoryUsage[i][1] < KILL_PROCESS:
                            i += 1
                            continue
                        logging.info(f'killing process {processes[i].name}')
                        kill_proc_tree(memoryUsage[i][0])
                        processes[i].terminate()
                        


                    total_memory = sum([m[1] for m in memoryUsage])
                    if total_memory > MEMORY_KILL:
                        memoryUsage.sort(key=lambda x: x[1], reverse=True)
                        process = [processes[i] for i in range(len(processes)) if processes[i].pid == memoryUsage[0][0]][0]
                        logging.info(f'killing process {process.name}')
                        kill_proc_tree(memoryUsage[0][0])

                    # empty write queue
                    while not writeQueue.empty():
                        solution: Solution = writeQueue.get()
                        resultsStore.insertItem(solution)
                        logging.info(f'saved solution {solution._id}')
                    
                    k = (k + 1) % 10
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
                    time.sleep(1.0)
                    while not writeQueue.empty():
                        solution: Solution = writeQueue.get()
                        resultsStore.insertItem(solution)
                        logging.info(f'saved solution {solution._id}')

            else:
                for exp in toExecute:
                    _run(exp, writeQueue)
                while not writeQueue.empty():
                    solution: Solution = writeQueue.get()
                    resultsStore.insertItem(solution)
                    logging.info(f'saved solution {solution._id}')
        except Exception:
            for process in processes:
                process.terminate()
                process.join()
            logging.exception('Fatal Exception)')
            logging.fatal('Fatal error terminating')
            return
        finally:
            resultsStore.close()
        logging.info('Finished all experiments')


def kill_proc_tree(pid, sig=signal.SIGTERM, include_parent=True,
                   timeout=None, on_terminate=None):
    """Kill a process tree (including grandchildren) with signal
    "sig" and return a (gone, still_alive) tuple.
    "on_terminate", if specified, is a callback function which is
    called as soon as a child terminates.
    """
    assert not (pid == os.getpid() and include_parent), "won't kill myself"
    try:
        parent = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return
    children = parent.children(recursive=True)
    if include_parent:
        children.append(parent)
    for p in children:
        try:
            p.send_signal(sig)
        except psutil.NoSuchProcess:
            pass
    gone, alive = psutil.wait_procs(
        children,
        timeout=timeout,
        callback=on_terminate
    )
    return (gone, alive)
