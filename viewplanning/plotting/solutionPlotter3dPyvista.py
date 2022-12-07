import numpy as np
import pyvista as pv
from viewplanning.dubins import vanaAirplaneCurve
from viewplanning.models import Region, Edge3D, Vertex3D
from .pathPlotter import SolutionPlotter
"""
Authors
-------
Collin Hague : chague@uncc.edu
"""


class SolutionPlotter3dPyvista(SolutionPlotter):
    """
    plots solution to path planning with object avoidance

    plot(volumes: list[Region], edges: list[Edge3D])
    """

    def __init__(self, environment: pv.PolyData):
        self.environment = environment

    def plot(self, volumes: 'list[Region]', edges: 'list[Edge3D]', **kwargs):
        """
        plots solution to path planning with object avoidance

        Parameters
        ----------
        environment: PolyData
            environment the agent transverses
        start: ndarray
            start orientation of vehicle R^3 x S^2
        end: ndarray
            end orientation of vehicle R^3 x S^2
        paths: list[DubinsPaths]
            list of paths for the vehicle to follow
        """
        plotter = pv.Plotter()
        if self.environment is not None:
            plotter.add_mesh(self.environment, color='gray')
        i = 0
        for path in edges:
            poly = pv.PolyData()
            f = vanaAirplaneCurve(path)
            t = np.linspace(0, 1, 100)

            points = np.array([f(s) for s in t])
            poly.points = points
            cells = np.full((len(points) - 1, 3), 2, dtype=np.int_)
            cells[:, 1] = np.arange(0, len(points) - 1, dtype=np.int_)
            cells[:, 2] = np.arange(1, len(points), dtype=np.int_)
            poly.lines = cells
            poly['scalars'] = np.arange(poly.n_points)
            mesh = poly.tube(radius=5)
            plotter.add_mesh(mesh)
            s = pv.Sphere(radius=5, center=path.start.asPoint())
            plotter.add_mesh(s, color='green')
            i += 1
        for volume in volumes:
            reader = pv.get_reader(volume.file)
            vv = reader.read()
            t = np.eye(4)
            t[:3, :3] = np.array(volume.rotationMatrix)
            vv.transform(t)
            plotter.add_mesh(vv, color='white', show_edges=True, opacity=.2)
            s = pv.Sphere(radius=5, center=volume.points[0])
            plotter.add_mesh(s, color='red')
        plotter.show()

    def savePlot(self, path):
        pass
