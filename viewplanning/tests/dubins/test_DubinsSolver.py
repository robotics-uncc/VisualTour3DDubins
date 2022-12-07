from viewplanning.dubins import DubinsPath, RustDubinsCar
from viewplanning.models import DubinsPathType, Vertex2D
import numpy as np

TOLERANCE = .0005


def testNormalization():
    solver = DubinsPath()
    edge = solver.calculatePath(0, 100, np.pi, 100, 100, np.pi / 4, 50)


def testPi0():
    def failStr(x, y, expected, actual):
        return f'failed for point ({x}, {y}) expected {expected[-1].name} {expected} actual {actual[-1].name}' + \
            ' {actual}' + \
            f"""
def testCurveCurveCurve():
    solver = DubinsPath()
    a, b, c, cost, pathType = solver.calculatePath(0, 0, 0, {x}, {y}, 0, 1)
    assert abs(a - {expected.aParam}) < TOLERANCE
    assert abs(b - {expected.bParam}) < TOLERANCE
    assert abs(c - {expected.cParam}) < TOLERANCE
    assert abs(cost - {expected.cost}) < TOLERANCE
    assert pathType == {expected.pathType}
            """
    dubins = DubinsPath()
    rust = RustDubinsCar()
    x, y = np.meshgrid(np.linspace(-6, 6, 121), np.linspace(-6, 6, 121))
    for i in range(x.shape[0]):
        for j in range(y.shape[0]):
            py = dubins.calculatePath(0, 0, 0, x[i, j], y[i, j], 0, 1)
            rb = rust.calculatePath(0, 0, 0, x[i, j], y[i, j], 0, 1)

            # normal case
            if py.pathType == rb.pathType:
                assert py.aParam - rb.aParam < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.bParam - rb.bParam < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.cParam - rb.cParam < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.cost - rb.cost < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.pathType == rb.pathType, failStr(x[i, j], y[i, j], rb, py)
            # ccc paths have equal length
            elif rb.pathType == DubinsPathType.RLR and py.pathType == DubinsPathType.LRL or rb.pathType == DubinsPathType.LRL and \
                    py.pathType == DubinsPathType.RLR:
                assert py.cost - rb.cost < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.bParam - rb.bParam < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.aParam - rb.cParam < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.cParam - rb.aParam < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)


def test2Pi3():
    def failStr(x, y, expected, actual):
        return f'failed for point ({x}, {y}) expected {expected[-1].name} {expected} actual {actual[-1].name}' + \
            ' {actual}' + \
            f"""
def testCurveCurveCurve():
    solver = DubinsPath()
    a, b, c, cost, pathType = solver.calculatePath(0, 0, 0, {x}, {y}, 2* np.pi / 3, 1)
    assert abs(a - {expected.aParam}) < TOLERANCE
    assert abs(b - {expected.bParam}) < TOLERANCE
    assert abs(c - {expected.cParam}) < TOLERANCE
    assert abs(cost - {expected.cost}) < TOLERANCE
    assert pathType == {expected.pathType}
            """
    dubins = DubinsPath()
    rust = RustDubinsCar()
    x, y = np.meshgrid(np.linspace(-6, 6, 121), np.linspace(-6, 6, 121))
    for i in range(x.shape[0]):
        for j in range(y.shape[0]):
            py = dubins.calculatePath(0, 0, 0, x[i, j], y[i, j], 2 * np.pi / 3, 1)
            rb = rust.calculatePath(0, 0, 0, x[i, j], y[i, j], 2 * np.pi / 3, 1)

            # normal case
            if py.pathType == rb.pathType:
                assert py.aParam - rb.aParam < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.bParam - rb.bParam < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.cParam - rb.cParam < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.cost - rb.cost < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.pathType == rb.pathType, failStr(x[i, j], y[i, j], rb, py)
            # ccc paths have equal length
            elif rb.pathType == DubinsPathType.RLR and py.pathType == DubinsPathType.LRL or rb.pathType == DubinsPathType.LRL and \
                    py.pathType == DubinsPathType.RLR:
                assert py.cost - rb.cost < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.bParam - rb.bParam < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.aParam - rb.cParam < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.cParam - rb.aParam < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)


def testPi():
    def failStr(x, y, expected, actual):
        return f'failed for point ({x}, {y}) expected {expected[-1].name} {expected} actual {actual[-1].name}' + \
            '{actual}' + \
            f"""
def testCurveCurveCurve():
    solver = DubinsPath()
    a, b, c, cost, pathType = solver.calculatePath(0, 0, 0, {x}, {y}, np.pi, 1)
    assert abs(a - {expected.aParam}) < TOLERANCE
    assert abs(b - {expected.bParam}) < TOLERANCE
    assert abs(c - {expected.cParam}) < TOLERANCE
    assert abs(cost - {expected.cost}) < TOLERANCE
    assert pathType == {expected.pathType}
            """
    dubins = DubinsPath()
    rust = RustDubinsCar()
    x, y = np.meshgrid(np.linspace(-6, 6, 121), np.linspace(-6, 6, 121))
    for i in range(x.shape[0]):
        for j in range(y.shape[0]):
            py = dubins.calculatePath(0, 0, 0, x[i, j], y[i, j], np.pi, 1)
            rb = rust.calculatePath(0, 0, 0, x[i, j], y[i, j], np.pi, 1)

            # normal case
            if py.pathType == rb.pathType:
                assert py.aParam - rb.aParam < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.bParam - rb.bParam < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.cParam - rb.cParam < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.cost - rb.cost < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.pathType == rb.pathType, failStr(x[i, j], y[i, j], rb, py)
            # ccc paths have equal length
            elif rb.pathType == DubinsPathType.RLR and py.pathType == DubinsPathType.LRL or rb.pathType == DubinsPathType.LRL and \
                    py.pathType == DubinsPathType.RLR:
                assert py.cost - rb.cost < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.bParam - rb.bParam < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.cParam - rb.cParam < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
                assert py.aParam - rb.aParam < TOLERANCE, failStr(x[i, j], y[i, j], rb, py)
