import os
from typing import Callable
import uuid
import numpy as np
import subprocess
from .Tsp import TspSolver
from viewplanning.models import Vertex


class MatrixTspSubprocess(TspSolver):
    '''
    TSP solver with custom non bidirectional edge costs
    '''

    def writeFiles(self, id: uuid.UUID, vertices: 'list[Vertex]', edgeMatrix: Callable[[int, int], float]):
        numVertices = len(vertices)
        neighboorhoods = []
        i = -1
        for vertex in vertices:
            if len(neighboorhoods) <= 0 or neighboorhoods[i] != vertex.group:
                neighboorhoods.append(vertex.group)
                i += 1
        numNeighboorHoods = len(neighboorhoods)
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
                        f.write('{0:11d}'.format(np.iinfo(np.int32).max))
                        continue
                    cost = edgeMatrix(vertices[y], vertices[x])
                    if np.isinf(cost):
                        f.write('{0:11d}'.format(np.iinfo(np.int32).max))
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
        result = subprocess.run(
            [
                './GLKH_EXP',
                os.path.abspath('data/tmp/{0}/params.param'.format(id))
            ],
            cwd='subs/GLKH/',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            print(result.stdout)
            raise Exception(result.stderr)
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
        if os.path.exists('data/tmp/{0}/gtsp.gtsp'.format(id)):
            os.remove('data/tmp/{0}/gtsp.gtsp'.format(id))
        if os.path.exists('data/tmp/{0}/tour.tour'.format(id)):
            os.remove('data/tmp/{0}/tour.tour'.format(id))
        if os.path.exists('data/tmp/{0}/params.param'.format(id)):
            os.remove('data/tmp/{0}/params.param'.format(id))
        if os.path.exists('data/tmp/{0}'.format(id)):
            os.rmdir('data/tmp/{0}'.format(id))
