import os
import uuid
import subprocess
import numpy as np
from typing import Callable

from viewplanning.models import Vertex3D
from .Tsp import TspSolver


def euclideanDistance(x: Vertex3D, y: Vertex3D):
    return int(np.ceil(np.linalg.norm(x.asPoint() - y.asPoint())))


class BidirectionalFunctionTspSubprocess(TspSolver):
    '''
    use GLKH to solve a tsp where the edges are bidirectional
    '''
    def __init__(self):
        super().__init__()
        self.process: subprocess.Popen = None

    def writeFiles(self, id: uuid.UUID, vertices: 'list[Vertex3D]', distanceFunction: Callable[[Vertex3D, Vertex3D], float] = euclideanDistance):
        if not os.path.exists('data/tmp'):
            os.mkdir('data/tmp')
        os.mkdir('data/tmp/{0}'.format(id))
        os.chmod('data/tmp/{0}'.format(id), 0o777)
        groups = set([vertex.group for vertex in vertices])

        if '' in groups:
            groups.remove('')
        if None in groups:
            groups.remove(None)

        with open('data/tmp/{0}/params.param'.format(id), 'w') as f:
            problemFile = os.path.abspath('data/tmp/{0}/gtsp.gtsp'.format(id))
            outputFile = os.path.abspath('data/tmp/{0}/tour.tour'.format(id))
            f.write('PROBLEM_FILE={0}\n'.format(problemFile))
            f.write('OUTPUT_TOUR_FILE={0}\n'.format(outputFile))
            f.write('EOF\n')
            f.close()
        with open('data/tmp/{0}/gtsp.gtsp'.format(id), 'w') as f:
            f.write('NAME : PathPlanning\n')
            f.write('TYPE : GTSP\n')
            f.write('COMMENT : Dubins Path Planning\n')
            f.write('DIMENSION : {0}\n'.format(len(vertices)))
            f.write('GTSP_SETS : {0}\n'.format(len(groups)))
            f.write('EDGE_WEIGHT_TYPE : EXPLICIT\n')
            f.write('EDGE_WEIGHT_FORMAT : UPPER_ROW\n')
            f.write('EDGE_WEIGHT_SECTION :\n')
            for i in range(len(vertices)):
                for j in range(i + 1, len(vertices)):
                    f.write('{0:11d}'.format(distanceFunction(vertices[i].asPoint(), vertices[j].asPoint())))
                f.write('\n')
            f.write('GTSP_SET_SECTION\n')
            i = 0
            j = 0
            currentLabel = vertices[i].group
            f.write(' {0}'.format(i + 1))
            for vertex in vertices:
                if currentLabel != vertex.group:
                    currentLabel = vertex.group
                    i += 1
                    f.write('    -1\n {0}'.format(i + 1))
                f.write('{0:8d}'.format(j + 1))
                j += 1
            f.write('    -1\nEOF\n')
            f.close()

    def solve(self, id, vertices: 'list[Vertex3D]') -> 'list[Vertex3D]':
        self.process = subprocess.Popen(
            [
                './GLKH_EXP',
                os.path.abspath('data/tmp/{0}/params.param'.format(id))
            ],
            cwd='subs/GLKH/',
            stdout=subprocess.DEVNULL
        )
        result = self.process.wait()
        if result != 0:
            message = self.process.stderr.read()
            raise Exception(message.decode('utf-8'))
        with open('data/tmp/{0}/tour.tour'.format(id)) as f:
            state = 0
            pathVertices: list[Vertex3D] = []
            for line in f.readlines():
                if state == 0:
                    if line.startswith('TOUR_SECTION'):
                        state = 1
                elif state == 1:
                    if line.startswith('-1'):
                        state = 2
                        continue
                    i = int(line) - 1
                    pathVertices.append(vertices[i])
        return pathVertices

    def cleanUp(self, id):
        if os.path.exists('data/tmp/{0}/gtsp.gtsp'.format(id)):
            os.remove('data/tmp/{0}/gtsp.gtsp'.format(id))
        if os.path.exists('data/tmp/{0}/tour.tour'.format(id)):
            os.remove('data/tmp/{0}/tour.tour'.format(id))
        if os.path.exists('data/tmp/{0}/params.param'.format(id)):
            os.remove('data/tmp/{0}/params.param'.format(id))
        if os.path.exists('data/tmp/{0}'.format(id)):
            os.rmdir('data/tmp/{0}'.format(id))
        if self.process is not None and self.process.poll() is None:
            self.process.kill()
