from viewplanning.dubins import DubinsAirplane
from viewplanning.edgeSolver import makeCurve
from viewplanning.models import Edge3D, Vertex3D
import matplotlib.pyplot as plt
import numpy as np


def testLow():
    dubins = DubinsAirplane()
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


def testMediumLRSL():
    dubins = DubinsAirplane()
    start = Vertex3D(
        x=0,
        y=0,
        z=0,
        theta=-np.pi / 4,
        phi=0
    )
    end = Vertex3D(
        x=250,
        y=250,
        z=500,
        theta=np.pi,
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


def testMediumLRSR():
    dubins = DubinsAirplane()
    start = Vertex3D(
        x=0,
        y=0,
        z=0,
        theta=np.pi / 4,
        phi=0
    )
    end = Vertex3D(
        x=250,
        y=250,
        z=500,
        theta=0
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


def testMediumRLSL():
    dubins = DubinsAirplane()
    start = Vertex3D(
        x=0,
        y=0,
        z=0,
        theta=np.pi / 6,
        phi=0
    )
    end = Vertex3D(
        x=-250,
        y=-250,
        z=500,
        theta=-np.pi / 2,
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


def testMediumRLSR():
    dubins = DubinsAirplane()
    start = Vertex3D(
        x=0,
        y=0,
        z=0,
        theta=np.pi / 4,
        phi=0
    )
    end = Vertex3D(
        x=-250,
        y=-250,
        z=500,
        theta=3 * np.pi / 4,
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


def testMediumLSRL():
    dubins = DubinsAirplane()
    start = Vertex3D(
        x=0,
        y=0,
        z=0,
        theta=0,
        phi=0
    )
    end = Vertex3D(
        x=250,
        y=250,
        z=-500,
        theta=5 * np.pi / 6,
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


def testMediumLSLR():
    dubins = DubinsAirplane()
    start = Vertex3D(
        x=0,
        y=0,
        z=0,
        theta=0,
        phi=0
    )
    end = Vertex3D(
        x=250,
        y=250,
        z=-500,
        theta=-np.pi / 6,
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


def testMediumRSLR():
    dubins = DubinsAirplane()
    start = Vertex3D(
        x=0,
        y=0,
        z=0,
        theta=0,
        phi=0
    )
    end = Vertex3D(
        x=-250,
        y=-250,
        z=-500,
        theta=2 * np.pi / 3,
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


def testMediumRSRL():
    dubins = DubinsAirplane()
    start = Vertex3D(
        x=0,
        y=0,
        z=0,
        theta=0,
        phi=0
    )
    end = Vertex3D(
        x=-250,
        y=-250,
        z=-500,
        theta=-np.pi / 6
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
    dubins = DubinsAirplane()
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
    dubins = DubinsAirplane()
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


def testFailedToConverge():
    dubins = DubinsAirplane()

    start = Vertex3D(
        x=393.717,
        y=150.736,
        z=150,
        theta=0,
        phi=0
    )
    end = Vertex3D(
        x=249.759,
        y=-49.125,
        z=370.725,
        theta=np.pi / 2,
        phi=0
    )
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
        50,
        -0.3490658503988659,
        0.3490658503988659
    )
    plot(edge)


def plot(edge: Edge3D):
    curve = makeCurve(edge, n=1000)
    fig, ax = plt.subplots(1, 1)
    x = curve[:, 0]
    y = curve[:, 1]
    ax.plot(x, y)
    ax.quiver([edge.start.x, edge.end.x], [edge.start.y, edge.end.y], np.cos(
        [edge.start.theta, edge.end.theta]), np.sin([edge.start.theta, edge.end.theta]))
    # ax[1].plot(x, z)
    # ax[2].plot(y, z)
    plt.show()
