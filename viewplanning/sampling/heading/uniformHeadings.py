from .headingStrategy import HeadingStrategy
import numpy as np
from shapely.geometry import Polygon
import pyvista as pv


class UniformHeadings(HeadingStrategy):
    '''
    get heading angle uniformly spaced [0, 2pi] every 2pi/numHeadings radians
    '''
    def __init__(self, numHeadings: int, headingRange: 'list[float]'):
        super().__init__(numHeadings)
        self.headingRange = headingRange

    def getHeadings(self, point: np.ndarray, mesh: pv.PolyData = None, polygon: Polygon = None, **kwargs):
        return np.linspace(self.headingRange[0], self.headingRange[1] - (self.headingRange[1] - self.headingRange[0]) / self.numHeadings, self.numHeadings)
