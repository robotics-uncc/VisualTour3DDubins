import matplotlib.pyplot as plt
import math
from viewplanning.models import Edge, Edge2D, Edge3D, Vertex2D, Region, Vertex
import numpy as np

from viewplanning.models.dubinsPathType import DubinsPathType


class SolutionPlotter(object):
    def plot(self, regions: 'list[Region]', edges: 'list[Edge]', **kwargs):
        pass

    def savePlot(self, name):
        '''
        save plot to file

        Parameters
        ----------
        name: str
            name of the file
        '''
        plt.savefig(name)

    def close(self):
        '''
        Dispose of any plotting resouces
        '''
        plt.close()


def makeCurve(initalPoint, direction, length, radius, n=100):
    if direction:
        perp = initalPoint['theta'] + math.pi / 2
    else:
        perp = initalPoint['theta'] - math.pi / 2
    centerX = radius * math.cos(perp) + initalPoint['x']
    centerY = radius * math.sin(perp) + initalPoint['y']
    dTheta = length / radius
    start = initalPoint['theta'] + (-1 * math.pi / 2 if direction else math.pi / 2)
    if direction:
        stop = start + dTheta
    else:
        stop = start - dTheta
    t = np.linspace(start, stop, n)
    x = radius * np.cos(t) + centerX
    y = radius * np.sin(t) + centerY
    return x, y, initalPoint['theta'] + (dTheta if direction else -dTheta)


def makeLine(initialPoint, length, n=100):
    t = np.linspace(0, 1, n)
    x = initialPoint['x'] + length * t * np.math.cos(initialPoint['theta'])
    y = initialPoint['y'] + length * t * np.math.sin(initialPoint['theta'])
    return x, y, initialPoint['theta']


def plot2D(start, lengths: 'list[float]', type: str, radius: float, n):
    startDict = {
        'x': start.x,
        'y': start.y,
        'theta': start.theta
    }
    cost = sum(lengths)
    x = np.zeros(n)
    y = np.zeros(n)
    j = 0
    if cost <= 0:
        return x, y
    for i in range(len(type)):
        ch = type[i]
        length = lengths[i]
        l = int(np.floor(length * n / cost))
        if l == 0:  # insiginficant length
            dTheta = length / radius
            if ch == 'R':
                startDict['theta'] -= dTheta
            elif ch == 'L':
                startDict['theta'] += dTheta
            continue
        if ch == 'L':
            newX, newY, theta = makeCurve(startDict, True, length, radius, l)
        elif ch == 'R':
            newX, newY, theta = makeCurve(startDict, False, length, radius, l)
        elif ch == 'S':
            newX, newY, theta = makeLine(startDict, length, l)
        x[j: j + l] = newX
        y[j: j + l] = newY
        j += l
        startDict = {
            'x': newX[-1],
            'y': newY[-1],
            'theta': theta
        }
    while j < n:
        x[j] = x[j - 1]
        y[j] = y[j - 1]
        j += 1
    return x, y


def makePath2d(edge: Edge2D, n=100):
    lengths = [edge.aParam, edge.bParam, edge.cParam]
    x, y = plot2D(edge.start, lengths, edge.pathType.name, edge.radius, n)
    return x, y


def makePath3d(edge: Edge3D, n=100):
    lengths = [edge.aParam, edge.bParam, edge.cParam, edge.starParam]
    x, y = plot2D(edge.start, lengths, edge.pathType.name, edge.radius, n)
    zStart = Vertex2D(x=0, y=edge.start.z, theta=edge.start.phi)
    lengths = [edge.dParam, edge.eParam, edge.fParam]
    if edge.pathTypeSZ == 0:
        z = np.zeros_like(x)
    else:
        _, z = plot2D(zStart, lengths, edge.pathTypeSZ.name, edge.radiusSZ, n)
    return x, y, z
