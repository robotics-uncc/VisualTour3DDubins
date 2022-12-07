import os
import uuid
import subprocess
from .Tsp import TspSolver
from viewplanning.models import Vertex3D
from typing import Callable


class EuclideanTsp3DSubprocess(TspSolver):    
    def writeFiles(self, id: uuid.UUID, vertices: 'list[Vertex3D]', cost: Callable[[Vertex3D, Vertex3D], float]):

        groups = set([vertex.group for vertex in vertices])
        if '' in groups:
            groups.remove('')
        if None in groups:
            groups.remove(None)

        os.mkdir('data/tmp/{0}'.format(id))
        os.chmod('data/tmp/{0}'.format(id), 0o777)
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
            f.write('EDGE_WEIGHT_TYPE : EUC_3D\n')
            f.write('EDGE_WEIGHT_FORMAT : FUNCTION\n')
            f.write('NODE_COORD_TYPE : THREED_COORDS\n ')
            f.write('NODE_COORD_SECTION\n')
            for i in range(len(vertices)):
                f.write('{0:4d} {1:10.2f} {1:10.2f} {1:10.2f}\n'.format(i + 1, vertices[i].x, vertices[i].y, vertices[i].z))
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
        subprocess.run(
            [
                './GLKH_EXP',
                 os.path.abspath('data/tmp/{0}/params.param'.format(id))
            ],
            cwd='subs/GLKH/',
            stdout=subprocess.DEVNULL
        )
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
