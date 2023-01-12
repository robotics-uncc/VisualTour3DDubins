from typing import Iterator
from matplotlib.patches import Polygon
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d.art3d as a3
import geopandas as gpd
import numpy as np
from viewplanning.plotting.pathPlotter import plot2D, SolutionPlotter
from viewplanning.models import Edge2D, Vertex2D, Region
from viewplanning.sampling import iterateRegions


class SolutionPlotter2dRegions(SolutionPlotter):
    '''
    Plot 2D solutions
    '''

    def plot(self, regions: 'list[Region]', edges: 'list[Edge2D]', **kwargs):
        '''
        Plot 2D Solutions

        Parameters
        ----------
        regions: list[Region]
            list of regions to plot
        edges: list[Edges]
            list of edges to plot
        '''
        fig = plt.figure()
        ax = plt.gca()
        self._plotEdges(edges, ax)
        # self._plotVertex(vertices, ax)
        self._plotRegions(regions, ax)
        plt.show()

    def _plotEdges(self, edges: 'list[Edge2D]', ax: plt.Axes):
        maxCost = max(map(lambda x: x.cost, edges))
        for edge in edges:
            x, y = plot2D(edge.start, [edge.aParam, edge.bParam, edge.cParam], edge.pathType.name, edge.radius, 100)
            points = np.array([x, y]).T.reshape(-1, 2)
            segments = np.stack([points[:-1], points[1:]], axis=1)
            colorIndex = np.linspace(0, edge.cost / maxCost, x.shape[0])
            norm = plt.Normalize(0, 1)
            lc = a3.LineCollection(segments, cmap='turbo', norm=norm)
            lc.set_array(colorIndex)
            line = ax.add_collection(lc)

    def _plotVertex(self, samples: 'list[Vertex2D]', ax: plt.Axes):
        x = [vertex.x for vertex in samples]
        y = [vertex.y for vertex in samples]
        theta = [vertex.theta for vertex in samples]
        ax.quiver(x, y, np.cos(theta), np.sin(theta), width=.0025)

    def _plotRegions(self, regions: 'Iterator[Region]', ax: plt.Axes):
        for region in iterateRegions(regions):
            p = gpd.GeoSeries(region)
            p.plot(ax=ax, facecolor='g', edgecolor='k', alpha=.5)
