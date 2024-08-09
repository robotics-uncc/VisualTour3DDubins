from viewplanning.sampling.sampleHelpers import polygonFromBody
import numpy as np
import pyvista as pv
from shapely.geometry import Polygon


CUTOFF = .05


class HeadingStrategy:
    '''
    abstract type representing a method to find headings in a visibility volume
    '''
    def __init__(self, numHeadings: int, dwellDistance: float = 0, multiplyDwell=True):
        '''
        Parameters
        ----------
        numHeadings: int
            number of headings per point
        dwellDistnace: float
            distance to dwell in a visibility volume
        multiplyDwell: bool
            extend the dwell distance by a multiple of the number of visible targets
        '''
        self.numHeadings = numHeadings
        self.dwellDistance = dwellDistance
        self.multiplyDwell = multiplyDwell

    def getHeadings(self, point: np.ndarray, mesh: pv.PolyData = None, polygon: Polygon = None, **kwargs):
        '''
        Get headings from a polygon or mesh. Either mesh or polygon parameters must be passed.
        Parameters
        ----------
        point: np.ndarray
            point to get headings at
        mesh: pv.PolyData
            visibility volume
        polygon: Polygon
            horizontal slice of a visibility volume
        Returns
        -------
        np.ndarray 
            a set of sampled headings for the point
        '''
        if polygon is None and mesh is None:
            raise TypeError('Mesh and Polygon cannot both be None')
        if polygon is None and mesh is not None:
            polygon = polygonFromBody(point[2], mesh, cutoff=CUTOFF)
        if polygon is None:
            return []
        return self.getHeadingsHelper(point, self.numHeadings, polygon, **kwargs)

    def getHeadingsHelper(self, point: np.ndarray, numHeadings: int, polygon: Polygon, **kwargs):
        '''
            abstract method to override in subclasses to sample headings
        '''
        raise NotImplementedError()
