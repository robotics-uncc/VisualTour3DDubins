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
    plot 3D solutions
    """

    def __init__(self, environment: pv.PolyData):
        '''
        Parameters
        ----------
        environment: pv.PolyData
            environment to plot solutions in
        '''
        self.environment = environment

    def plot(self, volumes: 'list[Region]', edges: 'list[Edge3D]', **kwargs):
        """
        Parameters
        ----------
        volumes: list[Region]
            list of view volumes to plot
        edges: list[Edge3D]
            list of Dubins airplane paths to plot
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
        '''save plot not implemented'''
        pass
