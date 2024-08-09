import os
from typing import Callable
import uuid
import numpy as np
import subprocess
from .Tsp import TspSolver
from viewplanning.models import VertexMulti
import logging
import time
import shutil


TIMEOUT = 6 * 60 * 60
TOUR_FINISHED_TIMEOUT = 5 * 60
START_SLEEP = .01
MAX_SLEEP = 16


class OverlappingTspSubprocess(TspSolver):
    '''
    Use GLKH to solve a tsp with overlapping nodesets
    '''
    def __init__(self):
        super().__init__()
        self.process: subprocess.Popen = None
        self.timedout = False
        self.costs = None

    def writeFiles(self, id: uuid.UUID, vertices: 'list[VertexMulti]', edgeMatrix: Callable[[int, int], float]):
        numVertices = len(vertices)
        neighboorhoods = set()
        for vertex in vertices:
            neighboorhoods.add(vertex.group)
        numNeighboorHoods = len(neighboorhoods)

        if not os.path.exists('data/tmp'):
            os.mkdir('data/tmp')

        if os.path.exists('data/tmp/{0}'.format(id)):
            shutil.rmtree('data/tmp/{0}'.format(id))

        os.mkdir('data/tmp/{0}'.format(id))
        os.chmod('data/tmp/{0}'.format(id), 0o777)
        with open('data/tmp/{0}/params.param'.format(id), 'w') as f:
            problemFile = os.path.abspath('data/tmp/{0}/gtsp.gtsp'.format(id))
            outputFile = os.path.abspath('data/tmp/{0}/tour.tour'.format(id))
            f.write('PROBLEM_FILE={0}\n'.format(problemFile))
            f.write('OUTPUT_TOUR_FILE={0}\n'.format(outputFile))
            f.write('EOF\n')
            f.close()
        costs = np.ones([numVertices, numVertices])
        with open(problemFile, 'w') as f:
            f.write('NAME : PathPlanning\n')
            f.write('TYPE : AGTSP\n')
            f.write('COMMENT : Dubins Path Planning\n')
            f.write('DIMENSION : {0}\n'.format(numVertices))
            f.write('GTSP_SETS : {0}\n'.format(numNeighboorHoods))
            f.write('EDGE_WEIGHT_TYPE : EXPLICIT\n')
            f.write('EDGE_WEIGHT_FORMAT : FULL_MATRIX\n')
            f.write('EDGE_WEIGHT_SECTION\n ')
            for y in range(numVertices):
                for x in range(numVertices):
                    # overlapping node
                    if vertices[x].id == vertices[y].id and x != y:
                        f.write('{0:11d}'.format(0))
                        costs[y, x] = 0
                        continue
                    # node in same set
                    if vertices[x].group in vertices[y].visits or vertices[y].group in vertices[x].visits:
                        f.write('{0:11d}'.format(np.iinfo(np.int32).max // numNeighboorHoods))
                        costs[y, x] = np.iinfo(np.int32).max // numNeighboorHoods
                        continue
                    cost = edgeMatrix(vertices[y], vertices[x])
                    # fail to calculate dubins path
                    if np.isinf(cost):
                        f.write('{0:11d}'.format(np.iinfo(np.int32).max // numNeighboorHoods))
                        costs[y, x] = np.iinfo(np.int32).max // numNeighboorHoods
                        continue
                    # write cost
                    f.write('{0:11d}'.format(round(cost)))
                    costs[y, x] = cost
                f.write('\n ')
            f.write('GTSP_SET_SECTION\n')
            i = 1
            for neighboorhood in neighboorhoods:
                f.write(' {0}'.format(i))
                for j in range(len(vertices)):
                    if neighboorhood == vertices[j].group:
                        f.write('{0:11d}'.format(j + 1))
                f.write('   -1\n')
                i += 1
            f.write('EOF\n')
            f.close()
            self.costs = costs

    def solve(self, id, vertices: 'list[VertexMulti]') -> 'list[VertexMulti]':
        self.timeout = False
        log = open(f'data/tmp/{id}/log.txt', 'wb')
        try:
            self.process = subprocess.Popen(
                [
                    './GLKH_EXP',
                    os.path.abspath('data/tmp/{0}/params.param'.format(id))
                ],
                cwd='subs/GLKH/',
                stdout=log,
                stderr=subprocess.PIPE
            )

            i = 0
            sleep = START_SLEEP
            result = self.process.poll()
            while result is None and i < TIMEOUT:
                i += sleep
                time.sleep(sleep)
                sleep = min(sleep * 2, MAX_SLEEP, TIMEOUT - i)
                result = self.process.poll()

            if i >= TIMEOUT and result is None:
                self.process.kill()
                result = 0
                logging.warning(f'killed process for id {id} after {i:.2f}s')
            elif result != 0:
                message = self.process.stderr.read()
                raise Exception(message.decode('utf-8'))
            else:
                logging.info(f'glkh took {i:.2f}s for {id}')
        finally:
            log.close()

        with open('data/tmp/{0}/tour.tour'.format(id)) as f:
            state = 0
            pathNodes: 'list[int]' = []
            for line in f.readlines():
                if state == 0:
                    if line.startswith('TOUR_SECTION'):
                        state = 1
                    if line.startswith('COMMENT : Length ='):
                        glkh_cost = int(line[18:])
                elif state == 1:
                    if line.startswith('-1'):
                        state = 2
                        continue
                    pathNodes.append(int(line) - 1)
        path = [vertices[i] for i in pathNodes]
        i = 0
        while i < len(path) - 1:
            path[i].visits.add(path[i].group)
            if path[i].id == path[i + 1].id:
                path[i].visits.add(path[i + 1].group)
                path.pop(i + 1)
            else:
                i += 1
        e = len(path) - 1
        path[e].visits.add(path[e].group)
        if path[0].id == path[e].id:
            path[0].visits.add(path[e].group)
            path.pop(e)
        cost = sum([self.costs[pathNodes[i - 1], pathNodes[i]] for i in range(len(pathNodes))])
        if np.abs(cost - glkh_cost) / cost > .01 or cost > np.iinfo(np.int32).max // len(set([v.group for v in vertices])):
            raise Exception('GLKH Solving Error')
        return path

    def cleanUp(self, id):
        for file in os.listdir(f'data/tmp/{id}/'):
            os.remove(f'data/tmp/{id}/' + file)
        if os.path.exists('data/tmp/{0}'.format(id)):
            os.rmdir('data/tmp/{0}'.format(id))
        if self.process is not None and self.process.poll() is None:
            self.process.kill()
            self.timedout = True
        if self.process is not None and self.process.poll() is None:
            self.process.kill()
            self.timedout = True
