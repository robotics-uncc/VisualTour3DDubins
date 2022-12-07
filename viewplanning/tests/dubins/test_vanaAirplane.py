from viewplanning.dubins import VanaAirplane
from viewplanning.plotting import makePath3d
from viewplanning.models import Edge3D, Vertex3D
import matplotlib.pyplot as plt
import numpy as np
import time


def testSpeed():
    dubins = VanaAirplane()
    radius = 40
    faMin = -np.pi / 12
    faMax = np.pi / 9
    start = Vertex3D(x=200, y=500, z=200, theta=np.pi, phi=-np.pi / 72)
    end = Vertex3D(x=500, y=350, z=100, theta=0, phi=-np.pi / 72)
    s = time.perf_counter_ns()
    edge = dubins.calculatePath(
        start.x,
        start.y,
        start.z,
        start.theta,
        start.phi,
        end.x,
        end.y,
        end.z,
        end.theta,
        end.phi,
        radius,
        faMin,
        faMax
    )
    t = (time.perf_counter_ns() - s) / 1e9
    with open('test.log', 'w') as f:
        f.write(f'long 1 length {edge.cost} time {t}\n')
    start = Vertex3D(x=100, y=-400, z=100, theta=np.pi / 6, phi=0)
    end = Vertex3D(x=500, y=-700, theta=5 * np.pi / 6, phi=0)
    start = Vertex3D(x=-200, y=200, z=250, theta=4 * np.pi / 4, phi=np.pi / 12)
    end = Vertex3D(x=500, y=800, z=0, theta=np.pi / 4, phi=np.pi / 12)
    start = Vertex3D(x=-300, y=1200, z=350, theta=8 * np.pi / 9, phi=0)
    end = Vertex3D(x=1000, y=200, z=0, theta=np.pi / 6, phi=0)
    start = Vertex3D(x=-500, y=-300, z=600, theta=5 * np.pi / 6, phi=np.pi / 36)
    end = Vertex3D(x=1200, y=900, z=100, theta=5 * np.pi / 3, phi=np.pi / 36)


def testLow():
    dubins = VanaAirplane()
    start = Vertex3D(
        x=0,
        y=0,
        z=0,
        theta=0,
        phi=0
    )
    end = Vertex3D(
        x=100,
        y=100,
        z=10,
        theta=-np.pi,
        phi=0
    )
    radius = 50
    flightAngle = 2 * np.pi / 9
    edge = dubins.calculatePath(
        start.x,
        start.y,
        start.z,
        start.theta,
        start.phi,
        end.x,
        end.y,
        end.z,
        end.theta,
        end.phi,
        radius,
        -flightAngle,
        flightAngle
    )
    plot(edge)


def testMediumCCC():
    dubins = VanaAirplane()
    start = Vertex3D(
        x=0,
        y=0,
        z=0,
        theta=0,
        phi=0
    )
    end = Vertex3D(
        x=100,
        y=100,
        z=150,
        theta=np.pi / 4,
        phi=0
    )
    radius = 50
    flightAngle = 2 * np.pi / 9
    edge = dubins.calculatePath(
        start.x,
        start.y,
        start.z,
        start.theta,
        start.phi,
        end.x,
        end.y,
        end.z,
        end.theta,
        end.phi,
        radius,
        -flightAngle,
        flightAngle
    )
    plot(edge)


def testHigh():
    dubins = VanaAirplane()
    start = Vertex3D(
        x=0,
        y=0,
        z=0,
        theta=0,
        phi=0
    )
    end = Vertex3D(
        x=100,
        y=100,
        z=400,
        theta=np.pi / 4,
        phi=0
    )
    radius = 50
    flightAngle = 2 * np.pi / 9
    edge = dubins.calculatePath(
        start.x,
        start.y,
        start.z,
        start.theta,
        start.phi,
        end.x,
        end.y,
        end.z,
        end.theta,
        end.phi,
        radius,
        -flightAngle,
        flightAngle
    )
    plot(edge)


def plot(edge: Edge3D):
    x, y, z = makePath3d(edge, n=1000)
    fig, ax = plt.subplots(1, 2)
    ax[0].plot(x, y)
    ax[0].quiver([edge.start.x, edge.end.x], [edge.start.y, edge.end.y], np.cos(
        [edge.start.theta, edge.end.theta]), np.sin([edge.start.theta, edge.end.theta]))
    ax[1].plot(np.linspace(0, edge.aParam + edge.bParam + edge.cParam, len(z)), z)
    plt.show()
