import numpy as np
import pyvista as pv
from .helpers import getSegment, dwellHeadingSubsets
from shapely.geometry import Polygon
from .headingStrategy import HeadingStrategy


OFFSET_INTO_SHAPE = .1
APPROX_ZERO = .0001


class StraightDwellHeadings(HeadingStrategy):
    '''
    finds headings in a visiblity volume where the vehicle can travel dwellDistance or dwellDistance * (number of visible targets)
    '''
    def __init__(self, numHeadings: int = 1, numRays: int = 1, dwellDistance: float = 1, multiplyDwell: bool = True):
        '''
        Parameters
        ----------
        numHeadings: int
            number of headings per point
        dwellDistnace: float
            distance to dwell in a visibility volume
        multiplyDwell: bool
            extend the dwell distance by a multiple of the number of visible targets
        numRays: int
            number of directions to test at a point
        '''
        super().__init__(numHeadings, dwellDistance=dwellDistance, multiplyDwell=multiplyDwell)
        self.numRays = numRays
        self.dwellDistance = dwellDistance

    def getHeadingsHelper(self, point: np.ndarray, numHeadings: int, polygon: Polygon, dwellMultiplier: float = 1, **kwargs):
        dwellMultiplier = dwellMultiplier if self.multiplyDwell else 1
        s = getSegment(point, polygon)
        d = s[1] - s[0]
        n = np.matmul(d, [[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
        point += n / np.linalg.norm(n) * OFFSET_INTO_SHAPE
        headingSets = dwellHeadingSubsets(
            point, polygon, self.numRays, self.dwellDistance * dwellMultiplier)
        if len(headingSets) <= 0:
            return []
        totalRange = sum([e - s for s, e in headingSets])
        if totalRange == 0:
            return [headingSets[0][0]]
        dTheta = totalRange / max(numHeadings - 1, 1)
        theta = headingSets[0][0]
        i = 0
        headings = []
        while i < len(headingSets):
            headings.append(theta)
            theta += dTheta
            if theta - headingSets[i][1] > APPROX_ZERO:
                dt = theta - headingSets[i][1]
                i += 1
                if i < len(headingSets):
                    theta = headingSets[i][0] + dt
        return headings
