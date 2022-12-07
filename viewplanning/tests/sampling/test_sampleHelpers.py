from viewplanning.sampling.sampleHelpers import containsPoint2d
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
import numpy as np


def testPointInTriangle():
    p = orient(Polygon(shell=[[0, 0], [1, 0], [0, 1]]))
    point = [.25, .25]
    assert containsPoint2d(point, p)
    assert not containsPoint2d([1, 1], p)
    assert not containsPoint2d([.75, .5], p)


def testPointInCircle():
    n = 1000
    t = np.linspace(0, 2 * np.pi - 2 * np.pi / n, n)
    x = np.cos(t)
    y = np.sin(t)
    polygon = orient(Polygon(shell=np.array([x, y]).T))
    assert containsPoint2d([0, 0], polygon)
    assert not containsPoint2d([2, 0], polygon)
    assert not containsPoint2d([-2, 0], polygon)
    assert not containsPoint2d([.9, .9], polygon)
