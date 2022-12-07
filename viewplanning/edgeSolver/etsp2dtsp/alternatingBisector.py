from .etsp2Dtsp import Etsp2Dtsp
from viewplanning.models import Vertex3D
import numpy as np


class AlternatingBisector(Etsp2Dtsp):
    def findHeadings(self, vertices: 'list[Vertex3D]', faMin: float, faMax: float, r: float) -> 'list[Vertex3D]':
        for i in range(len(vertices)):
            vertices[i].theta, vertices[i].phi = self._bisectAnglePerpendicular(
                vertices[i - 1],
                vertices[i],
                vertices[(i + 1) % len(vertices)]
            )
        state = 0
        for i in range(len(vertices)):
            if state == 0:
                a = vertices[i - 1].asPoint()
                b = vertices[i].asPoint()
                dist = np.linalg.norm(a - b)
                if dist <= 4 * r:
                    state = 1
                    theta, phi = self._vectorAngle((b - a))
                    theta = (theta + 2 * np.pi) % (2 * np.pi)
                    phi = np.clip(phi, faMin, faMax)
                    vertices[i - 1].theta = theta
                    vertices[i - 1].phi = phi
                    vertices[i].theta = theta
                    vertices[i].phi = phi
            elif state == 1:
                state = 0
        return vertices

    def _bisectAnglePerpendicular(self, a: Vertex3D, b: Vertex3D, c: Vertex3D):
        vA = np.array([[a.x, a.y, a.z]])
        vB = np.array([[b.x, b.y, b.z]])
        vC = np.array([[c.x, c.y, c.z]])
        ba = vB - vA
        bc = vC - vB
        b = ba + bc
        psi = np.arctan2(b[0, 1], b[0, 0])
        gamma = np.arctan2(b[0, 2], np.linalg.norm(b[:2]))
        return psi, gamma

    def _vectorAngle(self, vector):
        theta = np.arctan2(vector[0, 1], vector[0, 0])
        phi = np.arctan2(vector[0, 2], np.linalg.norm(vector[0, :2]))  # phi in [-pi/2 to pi/2]

        return theta, phi
