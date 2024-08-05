from .etsp2Dtsp import Etsp2Dtsp
from viewplanning.models import Vertex3D
import numpy as np


class Alternating(Etsp2Dtsp):
    def findHeadings(self, vertices: 'list[Vertex3D]', faMin: float, faMax: float, r: float) -> 'list[Vertex3D]':
        for i in range(0, len(vertices) - 1, 2):
            ab = vertices[i].asPoint() - vertices[i - 1].asPoint()
            theta, phi = self._vectorAngle(ab)
            phi = np.clip(phi, faMin, faMax)
            vertices[i].theta = theta
            vertices[i].phi = phi
            vertices[i - 1].theta = theta
            vertices[i - 1].phi = phi
        if len(vertices) % 2 == 1:
            i = len(vertices)
            ab = vertices[i - 1].asPoint() - vertices[i - 2].asPoint()
            theta, phi = self._vectorAngle(ab)
            vertices[i - 2].theta = theta
            vertices[i - 2].phi = phi
        return vertices

    def _vectorAngle(self, vector):
        theta = np.arctan2(vector[0, 1], vector[0, 0])
        phi = np.arctan2(vector[0, 2], np.linalg.norm(vector[:, :2]))  # phi in [-pi/2 to pi/2]

        return theta, phi
