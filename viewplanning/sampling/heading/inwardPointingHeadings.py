from .headingStrategy import HeadingStrategy
from .helpers import getSegment
import numpy as np
from shapely.geometry import Polygon


class InwardPointingHeadings(HeadingStrategy):
    '''
    find headings pointing inside a visibility volume or polygon uniformly spaced
    '''
    def getHeadingsHelper(self, point: np.ndarray, numHeadings: int, polygon: Polygon, **kwargs):
        s = getSegment(point, polygon)
        d = s[1] - s[0]
        theta = np.arctan2(d[1], d[0])
        return np.linspace(theta, theta + np.pi, numHeadings)
