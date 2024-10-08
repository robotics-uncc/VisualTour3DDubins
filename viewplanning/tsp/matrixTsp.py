import os
from typing import Callable
import uuid
import numpy as np
import subprocess
from .Tsp import TspSolver
from viewplanning.models import Vertex
import time
import logging


TIMEOUT = 6 * 60 * 60
TOUR_FINISHED_TIMEOUT = 5 * 60
START_SLEEP = .01
MAX_SLEEP = 16


class MatrixTspSubprocess(TspSolver):
    '''
    Use GLKH to solve a TSP where the edges are directional
    '''
    def __init__(self):
        super().__init__()
        self.process: subprocess.Popen = None
        self.timedout = False

    def writeFiles(self, id: uuid.UUID, vertices: 'list[Vertex]', edgeMatrix: Callable[[int, int], float]):
        numVertices = len(vertices)
        neighboorhoods = []
        i = -1
        for vertex in vertices:
            if len(neighboorhoods) <= 0 or neighboorhoods[i] != vertex.group:
                neighboorhoods.append(vertex.group)
                i += 1
        numNeighboorHoods = len(neighboorhoods)

        if not os.path.exists('data/tmp'):
            os.mkdir('data/tmp')

        os.mkdir('data/tmp/{0}'.format(id))
        os.chmod('data/tmp/{0}'.format(id), 0o777)
        with open('data/tmp/{0}/params.param'.format(id), 'w') as f:
            problemFile = os.path.abspath('data/tmp/{0}/gtsp.gtsp'.format(id))
            outputFile = os.path.abspath('data/tmp/{0}/tour.tour'.format(id))
            f.write('PROBLEM_FILE={0}\n'.format(problemFile))
            f.write('OUTPUT_TOUR_FILE={0}\n'.format(outputFile))
            f.write('EOF\n')
            f.close()
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
                    if vertices[x].group == vertices[y].group:
                        f.write('{0:11d}'.format(np.iinfo(np.int32).max // numNeighboorHoods))
                        continue
                    cost = edgeMatrix(vertices[y], vertices[x])
                    if np.isinf(cost):
                        f.write('{0:11d}'.format(np.iinfo(np.int32).max // numNeighboorHoods))
                    else:
                        f.write('{0:11d}'.format(round(cost)))
                f.write('\n ')
            f.write('GTSP_SET_SECTION\n')
            i = 1
            j = 1
            for neighboorhood in neighboorhoods:
                f.write(' {0}'.format(i))
                for vertex in filter(lambda x: x.group == neighboorhood, vertices):
                    f.write('{0:11d}'.format(j))
                    j += 1
                f.write('   -1\n')
                i += 1
            f.write('EOF\n')
            f.close()

    def solve(self, id, vertices: 'list[Vertex]') -> 'list[Vertex]':
        self.timedout = False
        log = open(f'data/tmp/{id}/log.txt', 'wb')
        try:
            self.process = subprocess.Popen(
                [
                    './GLKH_EXP',
                    os.path.abspath('data/tmp/{0}/params.param'.format(id))
                ],
                cwd='subs/GLKH/',
                stderr=subprocess.PIPE,
                stdout=log
            )
            i = 0
            sleep = START_SLEEP
            result = self.process.poll()
            while result is None and i < TIMEOUT:
                result = self.process.poll()
                i += sleep
                time.sleep(sleep)
                sleep = min(sleep * 2, MAX_SLEEP, TIMEOUT - i)

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
                elif state == 1:
                    if line.startswith('-1'):
                        state = 2
                        continue
                    pathNodes.append(int(line) - 1)
        return [vertices[i] for i in pathNodes]

    def cleanUp(self, id):
        for file in os.listdir(f'data/tmp/{id}/'):
            os.remove(f'data/tmp/{id}/' + file)
        if os.path.exists('data/tmp/{0}'.format(id)):
            os.rmdir('data/tmp/{0}'.format(id))
        if self.process is not None and self.process.poll() is None:
            self.process.kill()
            self.timedout = True
