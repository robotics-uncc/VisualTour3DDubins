from math import sqrt
from viewplanning.models import DubinsPathType, Edge3D, Edge2D
"""
Authors
-------
Collin Hague : chague@uncc.edu
"""


def norm2(x0, y0, x1, y1):
    return sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)
